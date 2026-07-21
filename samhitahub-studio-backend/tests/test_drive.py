"""
Tests for the Google Drive integration.

Two layers are covered:

- `GoogleDriveRepository`, tested directly against a fake Drive API
  client (`_FakeDriveResource`) that mimics the small slice of the
  `googleapiclient` `Resource` interface the repository actually uses
  (`files().list()` / `files().get()`), so the recursive-scan and
  path-building logic is verified without any real network access.
- The `/api/v1/drive/books` and `/api/v1/drive/book/{fileId}`
  endpoints, tested end-to-end via the ASGI test client with
  `get_drive_repository` overridden, following the same
  `app.dependency_overrides` pattern the codebase is designed around.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

import pytest
import pytest_asyncio
from googleapiclient.errors import HttpError
from httpx import ASGITransport, AsyncClient

from app.core.config import Environment, Settings
from app.main import create_app
from app.modules.google_drive.client import GoogleDriveError, get_google_drive_client
from app.modules.google_drive.schemas import DriveFile
from app.repositories.drive_repository import GoogleDriveRepository
from app.services.drive_service import DriveService


# ---------------------------------------------------------------------------
# Fake Google Drive API client
# ---------------------------------------------------------------------------


class _FakeExecutable:
    """Mimics the `.execute()`-returning object every `googleapiclient`
    request builder method (`list()`, `get()`) returns.
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def execute(self) -> dict[str, Any]:
        return self._payload


class _FakeFilesResource:
    """Mimics `Resource.files()`.

    `items_by_parent` maps a folder ID to the list of raw Drive file
    dicts (folders and files alike) that are direct children of that
    folder. `items_by_id` maps every file/folder ID to its own raw dict,
    used to answer `files().get(fileId=...)` calls.
    """

    def __init__(self, items_by_parent: dict[str, list[dict[str, Any]]]) -> None:
        self._items_by_parent = items_by_parent
        self._items_by_id: dict[str, dict[str, Any]] = {}
        for children in items_by_parent.values():
            for item in children:
                self._items_by_id[item["id"]] = item

    def list(
        self,
        *,
        q: str,
        spaces: str | None = None,
        fields: str | None = None,
        pageToken: str | None = None,
        pageSize: int | None = None,
    ) -> _FakeExecutable:
        folder_id = q.split("'")[1]
        mime_type = q.rsplit("mimeType = '", 1)[1].rstrip("'")
        children = self._items_by_parent.get(folder_id, [])
        matching = [item for item in children if item["mimeType"] == mime_type]
        return _FakeExecutable({"files": matching})

    def get(self, *, fileId: str, fields: str | None = None) -> _FakeExecutable:
        item = self._items_by_id.get(fileId)
        if item is None:
            error_response = SimpleNamespace(status=404, reason="Not Found")
            raise HttpError(resp=error_response, content=b"File not found")
        return _FakeExecutable(item)


class _FakeDriveResource:
    """Mimics the top-level `googleapiclient.discovery.Resource` returned
    by `build("drive", "v3", ...)`.
    """

    def __init__(self, items_by_parent: dict[str, list[dict[str, Any]]]) -> None:
        self._files = _FakeFilesResource(items_by_parent)

    def files(self) -> _FakeFilesResource:
        return self._files


def _folder(item_id: str, name: str, *, parents: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": item_id,
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": parents or [],
    }


def _pdf(item_id: str, name: str, *, parents: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": item_id,
        "name": name,
        "mimeType": "application/pdf",
        "modifiedTime": "2026-01-01T00:00:00.000Z",
        "size": "12345",
        "parents": parents or [],
    }


@pytest.fixture
def drive_tree() -> dict[str, list[dict[str, Any]]]:
    """A small Drive tree:

    root ("Scriptures")
    ├── book1.pdf
    └── Chapter 1 (subfolder)
        └── book2.pdf
    """
    return {
        "root": [
            _pdf("file-1", "book1.pdf", parents=["root"]),
            _folder("sub-1", "Chapter 1", parents=["root"]),
        ],
        "sub-1": [
            _pdf("file-2", "book2.pdf", parents=["sub-1"]),
        ],
    }


@pytest.fixture
def fake_client(drive_tree: dict[str, list[dict[str, Any]]]) -> _FakeDriveResource:
    client = _FakeDriveResource(drive_tree)
    # `_get_folder_name` looks up the root folder itself via files().get().
    client.files()._items_by_id["root"] = {"id": "root", "name": "Scriptures"}
    return client


@pytest.fixture
def repository(fake_client: _FakeDriveResource) -> GoogleDriveRepository:
    return GoogleDriveRepository(client=fake_client)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Repository tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_pdf_files_recursively_finds_all_pdfs(
    repository: GoogleDriveRepository,
) -> None:
    files = await repository.list_pdf_files("root")

    assert {f.file_id for f in files} == {"file-1", "file-2"}


@pytest.mark.asyncio
async def test_list_pdf_files_builds_drive_path_including_subfolders(
    repository: GoogleDriveRepository,
) -> None:
    files = await repository.list_pdf_files("root")

    by_id = {f.file_id: f for f in files}
    assert by_id["file-1"].drive_path == "Scriptures/book1.pdf"
    assert by_id["file-2"].drive_path == "Scriptures/Chapter 1/book2.pdf"


@pytest.mark.asyncio
async def test_list_pdf_files_sets_parent_folder_and_parses_size(
    repository: GoogleDriveRepository,
) -> None:
    files = await repository.list_pdf_files("root")

    by_id = {f.file_id: f for f in files}
    assert by_id["file-1"].parent_folder == "root"
    assert by_id["file-2"].parent_folder == "sub-1"
    assert by_id["file-1"].size == 12345


@pytest.mark.asyncio
async def test_get_pdf_file_returns_matching_file(repository: GoogleDriveRepository) -> None:
    file = await repository.get_pdf_file("file-2")

    assert file is not None
    assert isinstance(file, DriveFile)
    assert file.name == "book2.pdf"
    assert file.parent_folder == "sub-1"
    assert file.drive_path == "Scriptures/Chapter 1/book2.pdf"


@pytest.mark.asyncio
async def test_get_pdf_file_returns_none_when_not_found(
    repository: GoogleDriveRepository,
) -> None:
    file = await repository.get_pdf_file("does-not-exist")

    assert file is None


@pytest.mark.asyncio
async def test_get_pdf_file_returns_none_for_non_pdf_mime_type(
    fake_client: _FakeDriveResource,
) -> None:
    fake_client.files()._items_by_id["doc-1"] = {
        "id": "doc-1",
        "name": "notes.gdoc",
        "mimeType": "application/vnd.google-apps.document",
    }
    repository = GoogleDriveRepository(client=fake_client)  # type: ignore[arg-type]

    file = await repository.get_pdf_file("doc-1")

    assert file is None


# ---------------------------------------------------------------------------
# Client dependency tests
# ---------------------------------------------------------------------------


def test_get_google_drive_client_raises_when_not_configured() -> None:
    settings = Settings(environment=Environment.TEST, google_service_account_json_path=None)

    with pytest.raises(GoogleDriveError):
        get_google_drive_client(settings)


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class _StubRepository:
    def __init__(self, files: list[DriveFile]) -> None:
        self._files = files

    async def list_pdf_files(self, root_folder_id: str) -> list[DriveFile]:
        return self._files

    async def get_pdf_file(self, file_id: str) -> DriveFile | None:
        for file in self._files:
            if file.file_id == file_id:
                return file
        return None


@pytest.fixture
def sample_files() -> list[DriveFile]:
    return [
        DriveFile(
            file_id="file-1",
            name="book1.pdf",
            modified_time="2026-01-01T00:00:00.000Z",
            mime_type="application/pdf",
            size=100,
            parent_folder="root",
            drive_path="Scriptures/book1.pdf",
        )
    ]


@pytest.mark.asyncio
async def test_service_list_books_raises_when_root_folder_not_configured(
    sample_files: list[DriveFile],
) -> None:
    settings = Settings(environment=Environment.TEST, google_drive_root_folder_id=None)
    service = DriveService(settings=settings, repository=_StubRepository(sample_files))  # type: ignore[arg-type]

    with pytest.raises(GoogleDriveError):
        await service.list_books()


@pytest.mark.asyncio
async def test_service_list_books_maps_repository_files_to_responses(
    sample_files: list[DriveFile],
) -> None:
    settings = Settings(environment=Environment.TEST, google_drive_root_folder_id="root")
    service = DriveService(settings=settings, repository=_StubRepository(sample_files))  # type: ignore[arg-type]

    responses = await service.list_books()

    assert len(responses) == 1
    assert responses[0].file_id == "file-1"
    assert responses[0].drive_path == "Scriptures/book1.pdf"


@pytest.mark.asyncio
async def test_service_get_book_raises_not_found_for_missing_file(
    sample_files: list[DriveFile],
) -> None:
    from app.core.exceptions import NotFoundError

    settings = Settings(environment=Environment.TEST, google_drive_root_folder_id="root")
    service = DriveService(settings=settings, repository=_StubRepository(sample_files))  # type: ignore[arg-type]

    with pytest.raises(NotFoundError):
        await service.get_book("does-not-exist")


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def drive_client(sample_files: list[DriveFile]) -> AsyncIterator[AsyncClient]:
    """An HTTP client for an app with `get_drive_repository` overridden to
    return a stub repository, so endpoint tests never touch the real
    Google Drive API.
    """
    from app.repositories.drive_repository import get_drive_repository

    settings = Settings(
        environment=Environment.TEST,
        debug=True,
        log_json=False,
        google_drive_root_folder_id="root",
    )
    app = create_app(settings=settings)
    app.dependency_overrides[get_drive_repository] = lambda: _StubRepository(sample_files)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_books_endpoint_returns_camel_case_fields(
    drive_client: AsyncClient,
) -> None:
    response = await drive_client.get("/api/v1/drive/books")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["fileId"] == "file-1"
    assert body[0]["modifiedTime"] == "2026-01-01T00:00:00.000Z"
    assert body[0]["mimeType"] == "application/pdf"
    assert body[0]["parentFolder"] == "root"
    assert body[0]["drivePath"] == "Scriptures/book1.pdf"


@pytest.mark.asyncio
async def test_get_book_endpoint_returns_matching_file(drive_client: AsyncClient) -> None:
    response = await drive_client.get("/api/v1/drive/book/file-1")

    assert response.status_code == 200
    body = response.json()
    assert body["fileId"] == "file-1"
    assert body["name"] == "book1.pdf"


@pytest.mark.asyncio
async def test_get_book_endpoint_returns_404_for_missing_file(
    drive_client: AsyncClient,
) -> None:
    response = await drive_client.get("/api/v1/drive/book/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
