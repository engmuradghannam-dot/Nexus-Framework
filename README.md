# Nexus Framework

Enterprise-grade management platform combining **PMO**, **Industry Intelligence**, **AI Engine**, and **Regulatory Compliance** modules.

## Architecture

- **Backend**: Django 5 + DRF + PostgreSQL + Redis + Celery
- **Frontend**: React 19 + Vite + Tailwind CSS + Recharts + Framer Motion
- **Real-time**: Django Channels + WebSocket ready
- **Docs**: OpenAPI/Swagger auto-generated

## Modules

| Module | Features |
|--------|----------|
| **Core** | Users (HR-linked), Branches (Google Maps), Warehouses (sub-warehouses) |
| **PMO** | Projects, Tasks, Milestones, Budget tracking, Gantt-ready |
| **Industry** | Sectors, Companies, Metrics, Market cap analysis |
| **AI** | Model management, Predictions, Insights feed |
| **Regulatory** | Regulations, Compliance checks, Risk heatmap |

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # auto from env
python manage.py runserver

# Frontend
cd frontend
npm install
npm run dev
```

## API Documentation

Visit `/api/docs/` after running the backend.

## Superuser
- Email: `eng.murad.ghannam@gmail.com`
- Password: `ghannam2020`

## License
MIT
