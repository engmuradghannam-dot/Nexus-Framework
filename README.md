# Nexus Framework

Enterprise Management System with Django REST API and React Frontend.

## Modules
- **Core**: Companies, Branches, Warehouses, Sub-Warehouses, Departments, HR Profiles with Permissions
- **PMO**: Project Management - Projects, Tasks, Milestones
- **Industry**: Products, Inventory with Auto-Reorder, Suppliers, Purchase Orders
- **AI**: Groq API Integration - Conversations, Messages, Prompt Templates
- **Regulatory**: Regulations, Compliance Checks

## Features
- Google Maps location for Companies and Branches
- Auto-reorder system based on warehouse inventory levels
- Enhanced user permissions linked to HR department
- Multi-agent AI chat with Groq API

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## API Endpoints
- `/api/core/` - Core module
- `/api/pmo/` - PMO module
- `/api/industry/` - Industry module
- `/api/ai/` - AI module
- `/api/regulatory/` - Regulatory module
