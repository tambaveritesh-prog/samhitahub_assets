"""
Modules package.

Home for self-contained integrations with external systems/domains:
`ai`, `google_drive`, `firestore`, and (later) `ocr`. Each module is
structured as a near-independent sub-package so it can be developed,
tested, and reasoned about in isolation.

Why separate from `services`?
------------------------------
`services` orchestrate *use cases* ("detect chapters in this PDF and
publish the result"). `modules` provide the low-level *capability*
("call the Google Drive API", "call the AI provider", "write a
Firestore document"). A service composes one or more modules; a module
should not need to know about services, repositories, or the API layer.

Each module sub-package currently contains only an `__init__.py` and a
`README.md` describing its planned responsibilities and interface. No
functionality is implemented at this stage — see the top-level project
README for the phased build-out plan.
"""
