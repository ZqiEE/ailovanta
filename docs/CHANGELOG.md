# Ailovanta Changelog

## v1.5 Runtime Store MVP

- Added `api/runtime_store.py`.
- Moved runtime model registry from memory to SQLite.
- Moved runtime node registry from memory to SQLite.
- Added runtime assignment records.
- Added `/runtime/assignments`.
- Runtime status now reports storage path, route attempts, and successful routes.
- Updated API runtime layer to use `RuntimeStore`.
- Updated tests to clear the persistent runtime store between cases.
- Bumped public version to `1.5.0-runtime-store`.

## v1.4 Runtime Router MVP

- Added `api/runtime_router.py`.
- Added runtime model manifest registry.
- Added runtime node profile registry.
- Added warm/cold cache-aware runtime routing.
- Added privacy-aware routing for private models.
- Added `/runtime/models/register`.
- Added `/runtime/models`.
- Added `/runtime/nodes/register`.
- Added `/runtime/nodes`.
- Added `/runtime/status`.
- Added `/runtime/route`.
- Added tests for warm runtime preference.
- Added tests for private model routing to trusted pools only.
- Updated API docs with runtime router examples.
- Bumped public version to `1.4.0-runtime-router`.

## v1.3 Public MVP Finalization

- Renamed the public project to Ailovanta.
- Renamed the public repository to `ZqiEE/ailovanta`.
- Added Ailovanta CI badge to README.
- Upgraded README into a complete project entry point.
- Added `/app` route to serve the public product page from FastAPI.
- Added `/dashboard` route to serve the local dashboard from FastAPI.
- Updated Dockerfile to include dashboard and brand documents.
- Expanded API documentation with curl examples.
- Added project status boundary documentation.
- Added public launch checklist.
- Added contributing guide.
- Added issue templates and pull request template.
- Tightened repository validation checks.
- Added public MVP version file.

## v1.2 Dashboard Pack

- Added dashboard service.
- Added dashboard API endpoints.
- Added `dashboard.html`.
- Added dashboard tests.
- Added dashboard guide.

## v1.1 Operations Pack

- Added `/health`.
- Added `/ready`.
- Added queue maintenance script.
- Added training demo script.
- Added operations guide.
- Added developer handoff guide.

## v1.0 Engineering Pack

- Added Dockerfile.
- Added Docker Compose.
- Added Makefile.
- Added pytest tests.
- Added smoke test script.
- Added API reference.
- Added deployment guide.
- Added security notes.
- CI installs dependencies and runs validation plus tests.

## v0.9 Focused Training Jobs

- Added training job planner.
- Added training job API.
- Added model version registry.
- Removed unrelated scope from product positioning.

## v0.8 Queue and Verification

- Added result verification engine.
- Added verification records.
- Added retry failed jobs endpoint.
- Added requeue stale jobs endpoint.
