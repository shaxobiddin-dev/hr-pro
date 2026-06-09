# HR-Pro

**Human Resources & Payroll Management System**

O'zbekiston Mehnat Kodeksi va Soliq Kodeksiga mos HR va Payroll tizimi.

## Tech Stack

| Qatlam | Texnologiya |
|--------|-------------|
| Backend | Django 5.0 + DRF |
| Frontend | HTMX + Alpine.js + Tailwind CSS |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Task Queue | Celery |
| Web Server | Nginx + Gunicorn |

## Quick Start (Development)

### Local Development (Docker'siz)

```bash
# 1. Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Dependencies
pip install -r requirements/local.txt

# 3. Migrations
python manage.py migrate --settings=config.settings.local

# 4. Default data
python manage.py init_hr_data --settings=config.settings.local
python manage.py init_payroll_data --settings=config.settings.local

# 5. Superuser
python manage.py createsuperuser --settings=config.settings.local

# 6. Server
python manage.py runserver --settings=config.settings.local
```

### Docker Development

```bash
# 1. Environment
cp .env.example .env

# 2. Start containers
docker-compose up -d

# 3. Migrations
docker-compose exec web python manage.py migrate

# 4. Superuser
docker-compose exec web python manage.py createsuperuser

# 5. Open browser
open http://localhost:8000
```

## Production Deployment

```bash
# 1. Server tayorlash
cp .env.prod.example .env.prod
# .env.prod faylni to'ldiring

# 2. Deploy
./scripts/deploy.sh production

# 3. SSL sertifikat (Let's Encrypt)
# docker/nginx/ssl/ papkaga qo'ying
# docker/nginx/conf.d/hrpro.conf da SSL ni yoqing

# 4. Backup cronjob
# crontab -e
# 0 2 * * * /path/to/hr-pro/scripts/backup.sh daily
# 0 3 * * 0 /path/to/hr-pro/scripts/backup.sh weekly
```

## Makefile Commands

```bash
make help          # Barcha buyruqlar ro'yxati
make dev           # Local development server
make test          # Testlarni ishga tushirish
make lint          # Kod tekshirish
make migrate       # Migrations
make prod          # Production containers
make deploy        # Full deployment
make backup        # Database backup
make logs          # Container logs
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/v1/auth/token/` | JWT token olish |
| `/api/v1/hr/employees/` | Xodimlar CRUD |
| `/api/v1/hr/positions/` | Lavozimlar |
| `/api/v1/hr/levels/` | 10-darajali tizim |
| `/api/v1/org/departments/` | Bo'limlar |
| `/api/v1/payroll/periods/` | Ish haqi davrlari |
| `/api/v1/payroll/payrolls/` | Ish haqi hisob-kitoblari |
| `/api/docs/` | Swagger UI |
| `/health/` | Health check |

## Key Features

### HR Module
- **Employee Management** - Xodimlar CRUD, profil
- **Department Management** - Bo'limlar (ierarxik)
- **Position Management** - Lavozimlar, koeffitsiyentlar
- **10-Level System** - Professional darajalar (1.0-2.2 koef)
- **Tenure Brackets** - Staj koeffitsiyentlari

### Payroll Module
- **Salary Calculation** - MHTM × JOB_COEF × LEVEL_COEF × TENURE_COEF
- **Tax Deductions** - JSHDT (12%), INPS (0.1%)
- **Payroll Periods** - Oylik davrlar
- **Payslip Generation** - Ish haqi varaqasi
- **Bulk Processing** - Ommaviy hisoblash

### Admin Features
- **Dashboard** - Real-time statistika
- **User Management** - Foydalanuvchilar boshqaruvi
- **Audit Logs** - O'zgarishlar tarixi

## O'zbekiston Qonunchiligiga Moslik

| Qonun | Moslik |
|-------|--------|
| Mehnat Kodeksi | ✅ 127, 130, 157, 159, 196, 220, 222 moddalari |
| Soliq Kodeksi | ✅ JSHDT 12%, INPS 0.1%, Ijtimoiy soliq 12% |
| VM 314-son | ✅ Kasallik nafaqasi |
| MHTM | ✅ Minimal ish haqi (hozirgi: 1,200,000 so'm) |

## Project Structure

```
hr-pro/
├── apps/                   # Django applications
│   ├── core/              # Base models, mixins, health check
│   ├── accounts/          # User management
│   ├── employees/         # Employee, Position, Level
│   ├── departments/       # Departments (hierarchical)
│   ├── payroll/           # Salary calculation
│   └── ...
├── config/                # Django settings
│   ├── settings/
│   │   ├── base.py       # Base settings
│   │   ├── local.py      # Local development
│   │   ├── dev.py        # Docker development
│   │   └── prod.py       # Production
├── templates/             # HTML templates
├── docker/                # Docker files
│   ├── Dockerfile        # Development
│   ├── Dockerfile.prod   # Production (multi-stage)
│   ├── nginx/            # Nginx config
│   └── gunicorn.conf.py  # Gunicorn config
├── scripts/               # Deployment scripts
│   ├── deploy.sh
│   ├── backup.sh
│   └── restore.sh
└── docs/                  # Documentation
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Knowledge Base](docs/KNOWLEDGE.md)
- [Progress](docs/PROGRESS.md)

## License

Proprietary - All rights reserved

## Authors

- Development Team
