# HN Batch Analyzer (Django + DRF + LangGraph)

Fetch the top HN stories, extract article text, generate summaries, and create a bio‑tailored overview article. Background work runs via Huey (SQLite queue).

## Quickstart

1) Install deps
```bash
uv sync
```

2) Configure environment
Create `.env` in the project root:
```bash
OPENAI_API_KEY=your_key_here
# Optional
OPENAI_MODEL=gpt-5.2
SUMMARY_CONCURRENCY=5
OVERVIEW_MAX_TOKENS=3000
```

3) Migrate DB
```bash
uv run python manage.py migrate
```

4) (Optional) Admin login
```bash
uv run python manage.py createsuperuser
```
For the demo user: `admin` / `admin`.

5) Run the app (two terminals)
```bash
uv run python manage.py runserver
```
```bash
uv run python manage.py run_huey
```

Open: http://127.0.0.1:8000

## How it works

- **Fetch batch**: pulls top HN stories, stores metadata + extracted text.
- **Summaries**: generated once per story (bio‑agnostic).
- **Overview**: generated per `(batch, bio_hash)` using the summaries and the bio text.

## API endpoints (used by the UI)

- `POST /api/jobs/fetch-batch/` → `{job_id}`
- `POST /api/jobs/analyze/` with `{ "bio": "..." }` → `{job_id}`
- `GET /api/jobs/<job_id>/`
- `GET /api/batches/latest/` (optional `?bio_hash=...`)
- `GET /api/batches/<n>/`

## Notes

- SQLite data and Huey queue files are ignored via `.gitignore`.
- `.env` is loaded automatically in `config/settings.py`.
