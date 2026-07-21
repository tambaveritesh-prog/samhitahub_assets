# AI Module (Placeholder)

## Purpose
Encapsulates all interaction with AI providers used for automating
SamhitaHub Studio's content pipeline.

## Planned responsibilities
- **Chapter detection** — identify chapter/section boundaries within
  extracted book text.
- **Shloka detection** — identify verse (shloka) boundaries and
  numbering within a chapter's text.
- **Reference merging** — reconcile/merge cross-references (e.g.
  commentary references, cross-edition references) attached to a
  shloka.
- **Structured JSON generation** — convert detected chapters/shlokas
  into the final structured JSON schema consumed by the SamhitaHub
  Android app / Firestore.

## Planned structure (future stages)
```
app/modules/ai/
├── __init__.py
├── client.py          # Thin async wrapper around the AI provider SDK
├── prompts/            # Versioned prompt templates per task
├── chapter_detection.py
├── shloka_detection.py
├── reference_merging.py
└── schemas.py          # AI-task-specific input/output data shapes
```

## Design principles to follow when implementing
- The module exposes plain async functions/classes; it has no
  knowledge of FastAPI or HTTP.
- All provider credentials come from `app.core.config.Settings`
  (`ai_provider_api_key`, `ai_provider_model`), never read directly
  from the environment inside this module.
- Failures should raise a dedicated `AIProviderError(ExternalServiceError)`
  (subclassing `app.core.exceptions.ExternalServiceError`) so the
  existing exception-handling pipeline covers it automatically.
- Prompts should be versioned/tracked as code (not inlined ad hoc)
  since prompt changes materially affect output quality and need
  review/rollback like any other logic change.
