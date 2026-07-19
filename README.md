# Nexus Framework ERP

A modern, open-source ERP system built with Django + React.

## Features

- **14 Modules**: Core, PMO, Industry, AI, Regulatory, HR, E-commerce, Workflow, Permissions, Accounting, API Infrastructure, CRM, Sales, Audit
- **60+ Models** with full CRUD operations
- **397+ API Endpoints** (REST + GraphQL)
- **11 React Pages** with Material-UI
- **PWA Support** with offline capability
- **Multi-tenancy** with company scoping
- **Real-time** WebSocket support
- **Advanced Security** with field-level and record-level permissions

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
| API Infra | 5 | 46 | Webhooks, File Upload, Batch Ops |
| CRM | 4 | - | Customers, Contacts, Opportunities, Lead Scoring |
| Sales | 6 | - | Sales Orders, Quotations, Invoices, Deliveries, Backorders |
| Audit | 2 | - | CDHDR/CDPOS-style change log (who/when/old-value/new-value) across core models |

## License

MIT License - Free forever.
