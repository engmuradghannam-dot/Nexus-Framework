# Nexus Framework - Django ERP

Complete ERP system rebuilt with Django + DRF + PostgreSQL + Redis + Celery + React.

## Quick Start

```bash
# Clone and start
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Admin: http://localhost:8000/admin
```

## Modules
- ✅ Core (Users, Roles, Company, Branch, Warehouse)
- ✅ Accounts (Chart of Accounts, Journal Entries, Bank, Payments)
- ✅ Inventory (Items, Stock Entries, Warehouse Stock, Ledger)
- ✅ Buying (Suppliers, Purchase Orders, Receipts)
- ✅ Selling (Customers, Sales Orders, Delivery)
- ✅ Manufacturing (BOM, Work Orders, Job Cards)
- ✅ HR (Employees, Departments, Leave, Attendance)
- ✅ CRM (Leads, Opportunities)
- ✅ Projects (Projects, Tasks)
- ✅ Assets (Asset Categories, Assets)
- ✅ Workflow Engine

## API Endpoints
All endpoints at `/api/v1/` with full CRUD via DRF ViewSets.
