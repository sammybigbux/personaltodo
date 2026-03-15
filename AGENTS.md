# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

**Install dependencies**
```
pip install -r requirements.txt
```

**Run development server**
```
$env:DATABASE_URL="postgresql://user:pass@localhost/dbname"; flask run
```

**Run production server**
```
$env:DATABASE_URL="..."; gunicorn app:app
```

There is no build step, no test suite, and no linter configured in this project.

## Architecture

This is a single-user-per-session todo tracker with a Flask backend and a no-bundle React frontend.

**Backend (`app.py`)**
- Flask app with two REST endpoints: `GET /api/state` and `PUT /api/state`
- Requires `DATABASE_URL` environment variable (PostgreSQL connection string) — the app will crash on startup without it
- On startup, `init_db()` creates the `user_state` table if it doesn't exist (schema: `user_id TEXT PRIMARY KEY, state JSONB, updated_at TIMESTAMPTZ`)
- Each request requires an `x-user-id` header; missing it returns a 400 error
- State is stored as a JSONB blob of shape `{ tasks: [...], nextId: number }` — there is no row-per-task schema
- All routes except the two API routes fall through to `serve_frontend`, which serves `public/index.html`. The static folder is `public/`, so **`index.html` must be placed in a `public/` subdirectory** to be served correctly; the file currently at the root is the source of that page

**Frontend (`index.html` / `public/index.html`)**
- Pure client-side React 18 app loaded via CDN (no npm, no bundler, no build step)
- JSX is transpiled in the browser by `@babel/standalone` — edit the `<script type="text/babel">` block directly
- User identity is a UUID generated once and persisted in `localStorage` under the key `todo_user_id`; this UUID is sent as `x-user-id` on every API call
- On first load (empty state from API), the app seeds the DB with `INITIAL_TASKS` and saves them immediately
- Task list is always re-sorted before saving: incomplete tasks sorted by priority (High → Medium → Low), then completed tasks appended in completion order
- Task fields: `id` (integer, auto-incremented via `nextId`), `name`, `detail` (nullable), `time` (minutes), `priority` ("High" | "Medium" | "Low"), `deps` (free-text string, "None" if absent), `done` (boolean), `completedAt` (timestamp ms or null)
