# HR-Pro Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                               │
│                    (Browser / Mobile)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      CLOUDFLARE                              │
│                   (CDN + SSL + DDoS)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        NGINX                                 │
│                  (Reverse Proxy + Static)                    │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│      WEB UI (HTMX)      │     │      REST API (DRF)     │
│                         │     │                         │
│  /employees/            │     │  /api/v1/employees/     │
│  /payroll/              │     │  /api/v1/payroll/       │
│                         │     │                         │
│  → Django Templates     │     │  → JSON responses       │
│  → Session Auth         │     │  → JWT Auth             │
└─────────────────────────┘     └─────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                           │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │EmployeeSvc  │  │ PayrollSvc  │  │ AttendanceSvc       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  Business logic, calculations, validations                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       MODEL LAYER                            │
│                                                              │
│  Employee, Department, Position, Attendance, Leave,         │
│  Payroll, PayrollItem, Order, etc.                          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│   PostgreSQL    │ │    Redis    │ │     Celery      │
│   (Database)    │ │   (Cache)   │ │  (Background)   │
└─────────────────┘ └─────────────┘ └─────────────────┘
```

## Design Decisions

### 1. Hybrid Frontend Architecture

**Decision:** Django Templates + HTMX for Web UI, DRF for API

**Rationale:**
- Server-rendered HTML = faster First Contentful Paint
- HTMX = minimal JavaScript, Django-native
- DRF API = ready for future mobile app / integrations
- Single codebase, dual interface

### 2. Service Layer Pattern

**Decision:** Business logic in `services.py`, not in views

**Rationale:**
- Reusable logic between Web UI and API
- Easier testing
- Clear separation of concerns

### 3. O'zbekiston Localization

**Decision:** Full compliance with local laws

**Components:**
- MHTM-based salary calculation
- JSHDT, INPS, Social tax
- Mehnat Kodeksi-compliant HR orders
- Kasallik/Homiladorlik nafaqasi (VM 314, VM 796)

## Module Dependencies

```
core
  └── accounts
        └── employees
              ├── departments
              ├── attendance
              ├── leave
              └── payroll
                    └── orders
                          └── reports
```

## Data Flow

### Web UI Request
```
Browser → HTMX Request → Django View → Service → Model → DB
                                ↓
                         Template Render
                                ↓
Browser ← HTMX Swap ← HTML Partial ←
```

### API Request
```
Client → JWT Auth → DRF ViewSet → Service → Model → DB
                          ↓
                    Serializer
                          ↓
Client ← JSON Response ←
```

## Security

- Session auth for web (CSRF protected)
- JWT auth for API (short-lived tokens)
- Rate limiting on all endpoints
- Input validation via Django Forms / DRF Serializers
- SQL injection protection via ORM
- XSS protection via template auto-escaping
