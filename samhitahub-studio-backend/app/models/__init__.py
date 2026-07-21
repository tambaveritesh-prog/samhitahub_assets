"""
Models package.

Contains internal/domain and (later) persistence models — the data
structures that represent core business entities (e.g. `Book`,
`Chapter`, `Shloka`, `Reference`) as understood by the *backend itself*,
independent of how they're transported over HTTP.

Distinction from `app/schemas`:
- `models`  -> internal representation, potentially ORM/ODM-bound later
              (e.g. Firestore document models), used by services and
              repositories.
- `schemas` -> external representation (API request/response contracts),
              used by the `api` layer. Schemas often *derive from* or
              *map to* models but are allowed to diverge (e.g. hiding
              internal fields, reshaping for a specific endpoint).

Keeping these separate means the public API contract can stay stable
even if internal storage models change, and vice versa.
"""
