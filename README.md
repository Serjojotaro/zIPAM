# zIPAM

Open-source IP Address Management (IPAM) platform: strong IPv4/IPv6 management,
hierarchical prefixes, allocation with database-level correctness guarantees,
modern web UI.

> Status: (rc-01 cycle) — project scaffold, health endpoints and
> CI are in place; IPAM domain features are under development.

## Stack

- Backend: Python 3.12, Django 5, Django REST Framework, PostgreSQL 16
- Frontend: React + TypeScript (strict) + Vite + TailwindCSS
- Deployment: Docker Compose

## Quick start

```bash
cp .env.example .env   # edit secrets first
docker compose up -d --build
```

Open `http://localhost:8080` (configurable via `ZIPAM_WEB_PORT`).

- `GET /health` — process liveness
- `GET /ready` — readiness (includes database)

## Development

Backend:

```bash
cd backend
uv venv --python 3.12 .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
docker compose up -d db
export POSTGRES_HOST=localhost POSTGRES_PORT=5433 POSTGRES_DB=zipam \
       POSTGRES_USER=zipam POSTGRES_PASSWORD=<from .env>
python manage.py migrate
python manage.py runserver
ruff check . && mypy config core apps && pytest
```

Frontend:

```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173 (proxies /health,/ready,/api)
npm run lint && npm run typecheck && npm test
```

## Repository layout

```
backend/          Django project (config/, core/)
frontend/         Vite + React app
docs/             project documentation
docs/architecture/adr/   architecture decision records
```

## License

Apache License 2.0 — see `LICENSE.txt`.
