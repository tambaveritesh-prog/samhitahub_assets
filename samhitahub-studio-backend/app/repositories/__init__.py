"""
Repositories package.

Contains the data-access layer. A repository's job is to abstract
*persistence* (currently planned: Firestore) behind a plain Python
interface so that:

- Services depend on an abstract repository interface, not a concrete
  database SDK. This makes services testable with in-memory fakes and
  makes it possible to change the underlying store later without
  touching business logic.
- All query/write logic for a given entity lives in one place.

Convention: for each domain entity (e.g. `Book`), define:
- `BookRepository` (an abstract base class / `Protocol`) — the interface.
- `FirestoreBookRepository` (concrete implementation) — added when the
  Firestore module is implemented.
- `get_book_repository()` — a DI provider returning the concrete impl,
  so services just declare `repo: BookRepositoryDep` and don't care
  which implementation is wired up.
"""
