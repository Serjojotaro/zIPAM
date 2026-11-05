# zIPAM

[English](README.md) | [Русский](README.ru.md)

Open-source IP Address Management (IPAM) platform: strong IPv4/IPv6 management,
hierarchical prefixes, allocation with database-level correctness guarantees,
modern web UI.

> **Status (rc-01 cycle):** auth and role model, reference data, the IPAM core
> (prefixes, IP addresses, allocation/release, utilization, search), a working
> web UI and the Docker stack are usable today. The REST API is a **draft**
> (the contract stabilizes before 1.0.0); audit logging and OpenAPI come in the
> next cycle.

## Contents

- [User guide](#user-guide)
- [Administrator guide](#administrator-guide)
- [Developer guide](#developer-guide)
- [Repository layout](#repository-layout)
- [License](#license)

## What zIPAM does

- Tracks **prefixes** (networks) in a hierarchy derived from the address space
  itself — no manual tree maintenance, correctness enforced by PostgreSQL.
- Tracks **IP addresses** inside prefixes: allocate, reserve, release.
  Concurrent allocations are transactional: two requests can never get the
  same address.
- First-class **IPv4 and IPv6** (strict CIDR, RFC 5952 compression).
- **VRF** and **VLAN** support; ownership via organizations, tenants, regions,
  sites.
- Utilization visualization and an address grid for small prefixes.
- Global **search** by IP, CIDR or name.
- Session-based web UI with role-based access control; every operation is also
  available over the REST API.

---

# User guide

## Signing in

Open the application URL (by default `http://localhost:8080`) and sign in with
the username and password given by your administrator. The app remembers the
session in an HTTP-only cookie; use the **Log out** button in the top bar to
end it.

## Roles

| Role | Can do |
|---|---|
| **viewer** | browse everything; no create/edit/delete anywhere |
| **operator** | everything a viewer can, plus all operational work: create/edit prefixes, allocate/release addresses, manage reference data |
| **admin** | user and group management (via Django admin); also holds the other roles |

Roles are enforced on the backend — hiding buttons in the UI is never the only
protection. A write attempt without permission returns `403`.

## Core concepts

| Object | Meaning |
|---|---|
| **VRF** | an independent address space. Prefix and address uniqueness is enforced *per VRF*, so overlapping prefixes are fine in different VRFs. Optional Route Distinguisher (`rd`). |
| **Prefix** | a network in strict CIDR notation (e.g. `10.10.0.0/24` — host bits must be zero; `10.10.0.1/24` is rejected). Status: `active`, `reserved`, `container` (space holder that itself carries no hosts), `deprecated`. Optionally owned by a tenant and a site. |
| **IP address** | an allocation record inside a VRF. Status: `active`, `reserved`, `deprecated`. Deleting an address is the same as releasing it. |
| **VLAN** | `vid` 1–4094 with a name; unique by (vid, name). |
| **Organization / Tenant / Region / Site** | reference objects for ownership and location of prefixes. |

Prefixes form a hierarchy automatically from containment: `10.10.1.0/24` inside
`10.10.0.0/16` inside `10.0.0.0/8`. Parents, children, available space and
utilization are computed by the database, never by the client.

A typical workflow: create VRFs (or use the built-in `global` VRF) → create
top-level prefixes → optionally split them → allocate addresses as needed.

## Prefixes

**Prefixes** (the landing page) lists all prefixes with server-side
pagination.

- **Filters** — by VRF, by status, or **Contains**: enter any IP or CIDR
  (`10.0.0.5`, `10.0.0.0/24`) and you get its ancestors — a fast way to answer
  "which network does this address belong to?".
- **Create prefix** — pick a VRF (required), enter the prefix in strict CIDR
  (the form tells you when it is not strict), optionally set status, tenant,
  site and description. Duplicates inside a VRF are rejected.
- Click a row to open the **prefix detail** page.

## Prefix detail

The workbench for one prefix:

- **Breadcrumb** of its ancestors and **children** list.
- **Utilization bar** — allocated / total addresses, free count, percent.
- **Allocate address** — pick status and description; the service returns the
  next free address. Network and broadcast addresses (IPv4 ≤ `/30`) and the
  subnet-router anycast address (IPv6) are skipped automatically.
- **Address grid** — for prefixes up to 1024 addresses, every address is a
  colored cell. Click a free cell to allocate exactly that address; click an
  occupied cell to edit its status/description or release it.
- **Address table** — for any size (virtualized, paginated), so huge prefixes
  never freeze the UI.
- **Split prefix** — divide into children of a given prefix length. Allowed
  only while the prefix has no children and no allocated addresses.
- **Available subnets** — list of free space inside the prefix, optionally at
  a specific mask length (e.g. "give me free /26s").
- **Edit** status/description, or **Delete** the prefix (asks confirmation;
  its addresses are removed with it). Deleting a prefix that still has child
  prefixes is refused — delete children first.

## IP addresses

The **IP Addresses** page works across all prefixes:

- Filter by VRF, status, exact address, or **within** a CIDR.
- Tick rows and **Release selected** — a bulk operation that reports partial
  failures instead of silently skipping them.
- Edit status/description inline.
- Search results deep-link into this page with the address pre-filtered.

Addresses are usually created from a prefix page (allocate). To put a specific
address into inventory, click its cell in the address grid.

## Search

**Search** (`q` in the sidebar, minimum 2 characters) answers in groups:

- an IP address (`10.0.0.5`) → matching allocation plus the prefixes that
  contain it;
- a CIDR (`10.0.0.0/24`) → overlapping prefixes and addresses;
- free text → names of prefixes, VRFs, VLANs (by VID), organizations,
  tenants, regions, sites.

Every hit links straight to the owning page.

## VRFs, VLANs and reference data

**VRFs**, **VLANs**, **Organizations**, **Tenants**, **Regions** and **Sites**
are simple list + form pages: create, edit, delete. Two rules to remember:

- a VRF cannot be deleted while it still holds prefixes or addresses;
- a tenant/site/region/organization cannot be deleted while prefixes
  reference it (the API answers `409 REFERENCE_PROTECTED`).

## REST API (draft)

Everything the UI does is available under `/api/v1/`. The contract is draft
until 1.0.0. Quick map:

```
POST /api/v1/auth/login            GET  /api/v1/auth/me
GET  /api/v1/prefixes/?vrf=&status=&tenant=&site=&contains=&within=&parent=
GET  /api/v1/prefixes/{id}/utilization/
POST /api/v1/prefixes/{id}/allocate/          {"status": "active", "description": "..."}
POST /api/v1/prefixes/{id}/split/             {"prefix_len": 26}
POST /api/v1/prefixes/{id}/available-subnets/ {"masklen": 26}
GET  /api/v1/ip-addresses/?vrf=&status=&address=&within=
GET  /api/v1/search/?q=10.0.0.5
```

Session authentication with CSRF protection (the browser client handles both;
for scripting, fetch `GET /api/v1/auth/csrf` first and send the token in the
`X-CSRFToken` header). Errors use one envelope with stable machine-readable
codes — build integrations on the code, not the message:

```json
{
  "error": {
    "code": "IP_ALREADY_ALLOCATED",
    "message": "The requested IP address is already allocated.",
    "details": {}
  }
}
```

List endpoints are paginated (`page`, `page_size` up to 1024).

---

# Administrator guide

## Requirements

Docker with the Compose plugin. No other software is needed on the host.

## Install

```bash
cp .env.example .env    # then edit it — see the table below
docker compose up -d --build
```

Three containers come up: PostgreSQL 16, the Django backend, and nginx serving
the UI and proxying `/api`, `/health`, `/ready` to the backend. Open
`http://<host>:8080` (port configurable via `ZIPAM_WEB_PORT`).

## Configuration (`.env`)

| Variable | Default | Notes |
|---|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `zipam` / `zipam` / — | **set a real password**; the database volume persists it |
| `ZIPAM_PG_HOST_PORT` | `5433` | host port the database is published on |
| `DJANGO_SECRET_KEY` | — | **required**, ≥ 50 random characters, e.g. `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | production settings module is introduced later |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,backend,frontend` | add your hostname |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost:8080` | **must include the exact URL users open**, scheme + host + port (e.g. `http://localhost:8088`) — logins from browsers fail CSRF checks without it |
| `ZIPAM_WEB_PORT` | `8080` | published UI port |
| `ZIPAM_LOG_LEVEL` | `INFO` | |

## Users and roles

The application has no user-management UI yet; users are managed from the
command line:

```bash
# create a superuser (gets all roles)
docker compose exec backend python manage.py createsuperuser

# set a password
docker compose exec backend python manage.py changepassword <username>

# create a regular user and assign a role group
docker compose exec backend python manage.py shell -c '
from django.contrib.auth.models import User, Group
u = User.objects.create_user("alice", password="<password>")
u.groups.add(Group.objects.get(name="operator"))'
```

The three role groups (`viewer`, `operator`, `admin`) are created by a
migration; a superuser holds all roles implicitly. Django admin is not exposed
through the web proxy in the default Compose setup — manage users with the
commands above, or add a proxy location / publish port `8000` yourself if you
want it.

## Health and readiness

```
GET /health   process liveness
GET /ready    readiness, includes database connectivity
```

All three services have Docker health checks; `docker compose ps` shows the
state.

---

# Developer guide

## Stack

- Backend: Python 3.12, Django 5, Django REST Framework, PostgreSQL 16
- Frontend: React + TypeScript (strict) + Vite + TailwindCSS
- Quality gates: ruff, mypy, pytest / eslint, tsc, vitest

## Backend development

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

## Frontend development

```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173 (proxies /health,/ready,/api)
npm run lint && npm run typecheck && npm test
```

## Architecture in a nutshell

- Views stay thin; all business logic lives in per-app `services.py`
  (`allocate_ip`, `split_prefix`, `calculate_utilization`, …).
- Network correctness lives in PostgreSQL: custom `inet` fields with GiST
  indexes, hierarchy via the native operators (`>>`, `<<`, `&&`, …),
  uniqueness via `UNIQUE(vrf, prefix)` / `UNIQUE(vrf, address)`.
  Allocation takes a row lock on the prefix, so concurrent allocations are
  serialized — see the ADRs and `core/db/`.
- Domain errors map to stable codes via a shared `DomainError` and the
  §-documented error envelope.
- Frontend is feature-oriented (`src/features/...`); all contact with the
  table/virtualization library is isolated in a generic `DataTable`.

## Before opening a pull request

All gates must pass — CI runs the same set:

```bash
# backend
ruff check . && mypy config core apps && pytest
# frontend
npm run lint && npm run typecheck && npm test
# infra
docker compose build
```

## Repository layout

```
backend/          Django project (config/, core/, apps/)
frontend/         Vite + React app (src/app, components, features, pages)
LICENSE.txt       Apache-2.0
```

## License

Apache License 2.0 — see `LICENSE.txt`.
