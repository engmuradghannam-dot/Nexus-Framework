# Nexus Framework ERP

A modern, open-source ERP system built with Django + React.

## Features

- **14 Modules**: Core, PMO, Industry, AI, Regulatory, HR, E-commerce, Workflow, Permissions, Accounting, API Infrastructure, CRM, Sales, Audit
- **60+ Models** with full CRUD operations
- **397+ API Endpoints** (REST + GraphQL)
- **11 React Pages** with Material-UI
- **PWA Support** with offline capability
- **Multi-tenancy**: true database-per-tenant isolation (each tenant gets its own physical Postgres database) layered on top of the existing company-scoping model - see [Multi-tenancy](#multi-tenancy) below
- **Real-time** WebSocket support
- **Advanced Security** with field-level and record-level permissions
- **SAP-style document standards**: auto-numbered business documents (`JE-2026-00001`, `PO-2026-00001`, `MO-2026-00001`, `EMP-2026-00001`, ...), field-level validation (codes, names, phone/email, non-negative amounts, percentage ranges) on every master-data and transactional model, GL document balance checks (debit = credit before posting), and a universal CDHDR/CDPOS-style change log across master data and business documents

## Tech Stack

- **Backend**: Django 4.2, Django REST Framework, PostgreSQL, Redis, Celery
- **Frontend**: React 18, Material-UI, Recharts
- **API**: REST + GraphQL + WebSocket
- **DevOps**: Docker, Docker Compose, GitHub Actions

## Quick Start

```bash
# Clone
git clone https://github.com/engmuradghannam-dot/Nexus-Framework.git
cd Nexus-Framework

# Environment
cp .env.example .env
# Edit .env with your settings

# Docker
docker-compose up -d

# Migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Frontend
cd frontend && npm install && npm start
```

## API Documentation

- REST API: `/api/docs/`
- GraphQL: `/api/graphql/`

## Multi-tenancy

Two isolation models coexist:

- **Company scoping** (original, still the default): every domain model has a `company` FK (directly or via a relation), and `api_infra.scoping.CompanyScopedViewSet` filters every read/write to the companies the caller belongs to. This is what runs when no tenant is resolved for a request.
- **Database-per-tenant** (`api_infra.tenancy` / `api_infra.tenancy_router`): each `Tenant` can additionally get its own physical Postgres database. `TenantMiddleware` resolves the tenant for a request from its subdomain or an `X-Tenant` header, checks the caller is a verified member (`TenantUser`), and switches the active DB connection for the rest of the request to that tenant's database via a contextvar-based `DATABASE_ROUTERS` router.
  - Control-plane apps (`auth`, `contenttypes`, `sessions`, `admin`, `api_infra`, `audit`) always live in the `default` database - that's where the `Tenant`/`Domain`/`TenantUser` directory itself lives, and where the audit trail is centralized across tenants for platform admins.
  - Every other app is migrated into both `default` (so existing single-database usage, local dev, and the test suite are unaffected) and, once provisioned, each tenant's own database.
  - Provisioning (`Tenant.provision_database()`, or `python manage.py migrate_tenants` to (re-)provision every active tenant) clones `default`'s current schema via `pg_dump`/`psql` rather than replaying full Django migration history - several early migrations predate `db_constraint=False` being added to FKs that point at `auth.User`/`ContentType`, so replaying them against a database that never gets those shared tables fails. Cloning the already-converged schema and seeding migration bookkeeping to match `default` avoids that; future `migrate_tenants` runs then apply only new, forward migrations.
  - Known constraint: don't `select_related()`/`prefetch_related()` across the control-plane/tenant boundary (e.g. a tenant-scoped model's FK into `auth.User`) - Django compiles that as a single SQL JOIN against one connection, and the control-plane tables don't exist in a tenant's database. Plain (non-joined) FK access is unaffected, since each access is routed independently.

## Modules

| Module | Models | Endpoints | Description |
|--------|--------|-----------|-------------|
| Core | 6 | 44 | Companies, Branches, Warehouses |
| PMO | 3 | 23 | Projects, Tasks, Milestones |
| Industry | 6 | 37 | Products, Inventory, Suppliers |
| AI | 4 | 26 | Groq AI Integration |
| Regulatory | 2 | 14 | Compliance Tracking |
| HR | 8 | 53 | Employees, Payroll, Attendance |
| E-commerce | 9 | 41 | POS, Orders, Carts |
| Workflow | 4 | 29 | Approval Engine |
| Permissions | 5 | 32 | RBAC + Field/Record Level |
| Accounting | 8 | 52 | Invoices, Journal Entries, Reports |
| API Infra | 5 | 46 | Webhooks, File Upload, Batch Ops, Tenant directory + provisioning |
| CRM | 4 | - | Customers, Contacts, Opportunities, Lead Scoring |
| Sales | 6 | - | Sales Orders, Quotations, Invoices, Deliveries, Backorders |
| Audit | 2 | - | CDHDR/CDPOS-style change log (who/when/old-value/new-value) across core models |

## Local Development: Frontend/Backend Integration

The React dev server (`:3000`) and Django (`:8000`) are different origins, and the SPA authenticates with session cookies (`withCredentials: true`), not tokens - several settings have to line up for this to actually work, and it's easy to get a request that looks fine in the Network tab but fails silently:

- `CORS_ALLOW_CREDENTIALS = True` and `CORS_ALLOWED_ORIGINS` must include the frontend origin, or the browser rejects every cross-origin request outright (no error reaches your code, only the console).
- `CSRF_COOKIE_HTTPONLY = False` and `CSRF_TRUSTED_ORIGINS` must include the frontend origin, or every `POST`/`PUT`/`PATCH`/`DELETE` from the SPA gets a `403`.
- On the frontend, the axios instance needs `xsrfCookieName`/`xsrfHeaderName` **and** `withXSRFToken: true` - axios only auto-attaches the CSRF header for same-origin requests by default, and the API is a different origin (port) than the SPA.
- List endpoints use DRF's default pagination (`{count, next, previous, results}`); the axios response interceptor in `frontend/src/api.js` unwraps `results` transparently so page components can keep treating responses as plain arrays.

All of the above are already configured in this repo (`backend/nexus/settings.py`, `frontend/src/api.js`) - this section exists because every one of these was independently broken at some point and each failure mode looks different (CORS error, silent 403, blank page, "Invalid prop" warning), so if you're debugging a "the UI loads but nothing works" issue, check this list before assuming it's a new bug.

## Security Notes

- `POST /api/core/companies/` (creating a new top-level company) and the audit log (`/api/audit/change-headers/`) both require `is_staff` - creating a company isn't scoped by anything (it's the root of the scoping hierarchy), and the audit trail spans every company/tenant by design (see Multi-tenancy above), so both are treated as administrative operations rather than opened to every authenticated user.
- `Tenant.provision_database()` validates `schema_name` before using it in any DDL or shell-out to `pg_dump`/`psql`, and uses a properly quoted SQL identifier rather than string interpolation - `TenantViewSet.create_tenant` re-validates via `full_clean()` before persisting anything, since `Model.objects.create()` does not run model validators on its own.

## SAP Comparison (Gap Analysis)

An honest read against SAP S/4HANA / Business One, since that's the standard this codebase's conventions (auto-numbered documents, CDHDR/CDPOS, release-strategy-style approvals) already gesture toward.

**Closed in this pass:**
- Every module now has a real UI (CRM, Sales, Tenants, and the Audit Log had backends with zero frontend before this pass).
- A real login/logout flow - previously the SPA had no authentication screen of its own at all.
- The full request path actually works end-to-end (CORS, CSRF, session cookies, DRF pagination) - previously every single page failed to load any data.
- A liveness endpoint (`/health/`) and caching on the one endpoint hit on every dashboard load - baseline expectations for anything deployed behind a load balancer.
- Two endpoints (`TenantViewSet`, `TenantUserViewSet`) that had never worked at all (missing `serializer_class`, a pure oversight) and one that crashed on every single create (`SalesOrder.order_date` defaulting to a datetime on a date field).

**Realistically still open** (not attempted here - each is a multi-week-plus undertaking on its own, not a gap this pass could responsibly close):
- Real double-entry GL depth: sub-ledgers, period close, multi-currency revaluation, intercompany eliminations.
- A workflow/BPM designer with a visual editor, not just a fixed approval-chain model.
- Localization: multi-language UI, country-specific tax/statutory reporting.
- Query-level performance work beyond the one cache added here - several list endpoints iterate querysets in Python for aggregates (`sum(i.total for i in invoices)`) rather than using DB-side `Sum()`; fine at demo scale, worth revisiting under real data volume.
- A proper background job/queue dashboard (Celery is a dependency but has no operational visibility here).
- Formal RBAC administration UI for the field/record-level permission models that already exist on the backend.

## License

MIT License - Free forever.
