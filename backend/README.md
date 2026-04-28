# AI Team Backend

Phase 1 scope: authentication, project CRUD, artifact management, SQLAlchemy models, Alembic migration, and pytest coverage.
Phase 2 adds single-artifact review execution, aspect CRUD, finding response updates, LLM abstraction, and file parsers.

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

Create a local `.env` from `.env.example` and replace only placeholder values such as `JWT_SECRET_KEY=xxx` with environment-specific values. Do not commit real secrets.
Keep `LLM_PROVIDER=stub` for local tests. Use `LLM_PROVIDER=anthropic` only when `ANTHROPIC_API_KEY` is provided through the environment.

## Alembic

The Phase 1 and Phase 2 migration files are already generated under `alembic/versions`.

```powershell
alembic upgrade head
```

## Run API

```powershell
uvicorn app.main:app --reload
```

Open Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

## Test

```powershell
pytest
```

## Review API Example

Start the API with `LLM_PROVIDER=stub` for a deterministic local review. The review job ID is the created review ID.

```powershell
$env:LLM_PROVIDER = "stub"
uvicorn app.main:app --reload
```

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

curl -X POST http://127.0.0.1:8000/api/aspects \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Naming","target_phases":["PG"],"prompt_template":"Phase: {phase}\nAspect: {aspect_name}\nArtifact:\n{artifact_content}\nReturn JSON array with location, severity, content, suggestion.","default_severity":"mid"}'

curl -X POST http://127.0.0.1:8000/api/projects/${PROJECT_ID}/artifacts \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "phase=PG" \
  -F "file=@sample.py;type=text/x-python"

curl -X POST http://127.0.0.1:8000/api/projects/${PROJECT_ID}/reviews \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"artifact_id":"'"${ARTIFACT_ID}"'","aspect_ids":["'"${ASPECT_ID}"'"]}'

curl -H "Authorization: Bearer ${TOKEN}" \
  http://127.0.0.1:8000/api/reviews/${REVIEW_ID}

curl -H "Authorization: Bearer ${TOKEN}" \
  "http://127.0.0.1:8000/api/reviews/${REVIEW_ID}/findings?severity=high"

curl -X PUT http://127.0.0.1:8000/api/findings/${FINDING_ID}/response \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"status":"done","comment":"Fixed"}'
```

## Storage

Uploaded artifacts are stored below `storage/projects/{project_id}/{phase}/{filename}` relative to this backend directory. Artifact DELETE removes the database record; physical file removal is intentionally left out of Phase 1 to avoid irreversible file operations.
