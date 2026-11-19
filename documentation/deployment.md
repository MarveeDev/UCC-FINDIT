# UCC FINDIT — Deployment Guide

Target platforms: **Vercel** (frontend), **Render** (backend), **managed PostgreSQL** (database).

## Architecture

- Frontend: React + TypeScript + Vite (served statically). Talks to the backend via `/api` — in production, configure `VITE_API_BASE_URL` to the backend origin (e.g. `https://<backend>.onrender.com/api/v1`).
- Backend: Flask (gunicorn) + SQLAlchemy + Alembic. Serves the REST API under `/api/v1`.
- Database: PostgreSQL. The backend uses `DATABASE_URL` (SQLAlchemy URL, e.g. `postgresql+psycopg://user:pass@host:5432/ucc_findit`).

## Required environment variables

### Backend (Render)
| Variable | Development | Testing | Production |
|---|---|---|---|
| `FLASK_CONFIG` | `development` | `testing` | `production` |
| `SECRET_KEY` | any (dev placeholder ok) | any | **strong, ≥32 chars, unique** |
| `JWT_SECRET_KEY` | any | any | **strong, ≥32 chars, unique** |
| `DATABASE_URL` | `postgresql+psycopg://…` (or sqlite for local) | `sqlite:///:memory:` | `postgresql+psycopg://…` (PostgreSQL required) |
| `CORS_ORIGINS` | `http://localhost:5174` | — | **frontend origin** (never `*`) |
| `ENFORCE_UCC_DOMAIN` | `false` | `false` | `true` (after domain verified) |
| `UCC_EMAIL_DOMAINS` | `stu.ucc.edu.gh,ucc.edu.gh` | — | official domains |
| `CLOUDINARY_CLOUD_NAME` | — | — | **required** (Cloudinary cloud name) |
| `CLOUDINARY_API_KEY` | — | — | **required** (Cloudinary API key) |
| `CLOUDINARY_API_SECRET` | — | — | **required** (Cloudinary API secret) |
| `CLOUDINARY_FOLDER` | `ucc-findit/items` | — | Cloudinary folder prefix |
| `PORT` | 5000 | — | Render-provided |

Never commit real `.env` values. Secrets are provided via the hosting platform's secret store.

### Frontend (Vercel)
| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend origin, e.g. `https://<backend>.onrender.com/api/v1` (omit in dev; Vite proxies `/api` locally) |

## Commands

### Frontend
- Dev: `npm run dev`
- Build: `npm run build` (outputs `dist/`)
- Lint: `npm run lint`

Vercel build command: `npm run build`, output directory `dist`.

### Backend
- Dev: `.venv\Scripts\python run.py` (Windows) or `python run.py`
- Migrations: `flask --app run.py db upgrade head`
- Production start (Render): `gunicorn run:app` (add `gunicorn` to requirements; set `PORT` via Render)

## Health & readiness
- `GET /api/v1/health` — returns `200 {"status":"ok"}` when the API and database are reachable; `503` otherwise. Use as the Render health-check path.

## Security notes
- `FLASK_CONFIG=production` refuses to start with missing/weak `SECRET_KEY`/`JWT_SECRET_KEY`.
- `CORS_ORIGINS` must be the exact frontend origin(s); never `*` in production.
- Do **not** enable `X-Forwarded-For` trust unless behind a trusted reverse proxy (it is ignored by default).
- Registration creates the account directly; there is no email verification step. Password hashing, JWT authentication, rate limiting, and UCC email-domain validation remain enforced.
- File uploads use local disk by default; use object storage / persistent disk on Render (the filesystem is ephemeral).

## Backup & recovery
- Enable managed PostgreSQL automated backups.
- Backups are PostgreSQL dumps; restore with `pg_restore`, then re-run `flask db upgrade head` to match the app's migration head.

## PostgreSQL verification status
- PostgreSQL is not available in this environment, so no live database test has been run.
- All migrations have been verified **offline** against the PostgreSQL dialect (`flask db upgrade head --sql`), confirming `SERIAL`/`DOUBLE PRECISION`/`VARCHAR`/`TEXT`/`BOOLEAN`/`TIMESTAMP` types, foreign keys (`CASCADE`/`SET NULL`), unique constraints and partial indexes.
