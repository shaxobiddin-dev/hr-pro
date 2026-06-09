# HR-Pro Loyihasi Bilimlar Bazasi

> Bu fayl loyiha uchun zarur texnik ma'lumotlarni saqlaydi.
> Yangi ma'lumot topilsa shu yerga qo'shiladi.

---

## 1. HR Payroll Tizimi Arxitekturasi

### Asosiy Modullar
| Modul | Vazifasi |
|-------|----------|
| Employees | Xodimlar ma'lumotlari (CRUD) |
| Departments | Bo'limlar boshqaruvi |
| Positions | Lavozimlar |
| Attendance | Davomat (kirish/chiqish vaqti) |
| Leave | Ta'til va ruxsatlar |
| Payroll | Ish haqi hisoblash |
| Payslip | Oylik varaqalar |
| Recruitment | Ishga qabul |
| Performance | Samaradorlik baholash |

### Payroll Hisoblash Formulasi
```
Sof ish haqi = Asosiy maosh + Qo'shimchalar - Ushlanmalar - Soliqlar
```

**Manba:** [GeeksforGeeks - HRMS Database Design](https://www.geeksforgeeks.org/sql/how-to-design-a-database-for-human-resource-management-system-hrms/)

---

## 2. Database Schema (Asosiy Jadvallar)

### employees
```sql
- id (PK)
- employee_code (unique)
- first_name, last_name
- email, phone
- department_id (FK)
- position_id (FK)
- hire_date
- status (active/inactive)
- created_at, updated_at
```

### departments
```sql
- id (PK)
- name
- manager_id (FK -> employees)
- parent_id (FK -> departments, nullable)
```

### positions
```sql
- id (PK)
- title
- department_id (FK)
- base_salary
- grade_level
```

### attendance
```sql
- id (PK)
- employee_id (FK)
- date
- time_in, time_out
- lunch_out, lunch_in
- status (present/absent/late)
- worked_hours (calculated)
```

### leave_requests
```sql
- id (PK)
- employee_id (FK)
- leave_type (annual/sick/unpaid)
- start_date, end_date
- status (pending/approved/rejected)
- approved_by (FK -> employees)
```

### salary_components
```sql
- id (PK)
- name (bonus, tax, insurance)
- type (earning/deduction)
- is_percentage (boolean)
- value
```

### payroll
```sql
- id (PK)
- employee_id (FK)
- period_start, period_end
- gross_salary
- total_deductions
- net_salary
- status (draft/processed/paid)
```

### payroll_items
```sql
- id (PK)
- payroll_id (FK)
- component_id (FK)
- amount
```

**Manba:** [Medium - Payroll Management System Design](https://medium.com/@snyati/designing-a-payroll-management-system-using-relational-databases-a-real-world-application-of-sql-62bdd2157382)

---

## 3. O'zbekiston Soliq Stavkalari (2025)

| Soliq turi | Stavka |
|------------|--------|
| Daromad solig'i (JSHDS) | 12% |
| Ijtimoiy soliq | 12% (byudjet tashkilotlari - 25%) |
| QQS | 12% |
| Foyda solig'i | 15% |

### Imtiyozlar (2025-2028)
- Kambag'al oila a'zolarini ishga olgan korxonalar: ijtimoiy soliq **1%**
- Tikuv-trikotaj sanoati: daromad solig'i **1%** (shartlar mavjud)

**Manba:** [Gazeta.uz - 2025 soliq o'zgarishlari](https://www.gazeta.uz/oz/2025/01/10/taxes-2025/)

---

## 4. Django REST Framework Best Practices

### Authentication
- **Tavsiya:** `djangorestframework-simplejwt`
- Access token: qisqa muddatli (15-30 daqiqa)
- Refresh token: uzoq muddatli (7 kun)
- Token blacklisting yoqilgan bo'lsin

### Asosiy Paketlar
```
Django>=4.2
djangorestframework>=3.14
djangorestframework-simplejwt
dj-rest-auth
django-filter
drf-spectacular (OpenAPI)
django-cors-headers
```

### Security
- HTTPS majburiy
- CORS faqat ruxsat berilgan domainlar
- Rate limiting (throttling)
- Input validation

**Manba:** [Django REST Framework Docs](https://www.django-rest-framework.org/api-guide/authentication/)

---

## 5. CI/CD Pipeline (GitHub Actions)

### Workflow tuzilishi
```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements/dev.txt
      - name: Run linting
        run: ruff check .
      - name: Run tests
        run: pytest --cov

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        run: # deployment script
```

### GitHub Secrets (kerak bo'ladi)
- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `SERVER_HOST`
- `SERVER_USER`
- `SSH_PRIVATE_KEY`

**Manba:** [DigitalOcean - Django CI/CD](https://www.digitalocean.com/community/questions/advanced-django-ci-cd-pipeline-with-github-actions)

---

## 6. Loyiha Strukturasi

```
hr-pro/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── config/                 # Django settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/           # User authentication
│   ├── employees/          # Xodimlar
│   ├── departments/        # Bo'limlar
│   ├── attendance/         # Davomat
│   ├── leave/              # Ta'tillar
│   ├── payroll/            # Ish haqi
│   └── reports/            # Hisobotlar
├── tests/
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── CLAUDE.md
├── KNOWLEDGE.md
└── manage.py
```

---

## 7. Texnologiyalar Stack (TASDIQLANGAN)

### 7.1 Backend

| Paket | Versiya | Vazifa |
|-------|---------|--------|
| Python | 3.12+ | Asosiy til |
| Django | 5.0+ | Web framework |
| djangorestframework | 3.15+ | REST API |
| django-allauth | 0.60+ | Auth (login, register, social) |
| djangorestframework-simplejwt | 5.3+ | JWT tokens (API uchun) |
| celery | 5.4+ | Background tasks |
| redis | 5.0+ | Cache, Celery broker |
| psycopg | 3.1+ | PostgreSQL driver |
| django-filter | 24.0+ | API filtering |
| drf-spectacular | 0.27+ | OpenAPI docs |
| django-cors-headers | 4.3+ | CORS |
| gunicorn | 22.0+ | WSGI server |
| whitenoise | 6.6+ | Static files |
| sentry-sdk | 1.40+ | Error tracking |

### 7.2 Frontend (Django Templates + HTMX)

| Paket | Vazifa |
|-------|--------|
| **HTMX** | AJAX so'rovlar, partial updates, Django bilan ideal |
| **Alpine.js** | Minimal reaktivlik (dropdown, modal, tabs) |
| **Tailwind CSS** | Utility-first CSS, professional UI |
| **Heroicons** | SVG ikonlar |
| **Chart.js** | Grafiklar, diagrammalar |

**Nima uchun HTMX?**
- Django template bilan to'g'ridan ishlaydi
- JavaScript minimal (10x kam kod)
- SEO yaxshi (server-rendered HTML)
- Real-time interactivity
- O'rganish oson

### 7.3 Database

| Texnologiya | Vazifa |
|-------------|--------|
| **PostgreSQL 16** | Asosiy DB |
| **Redis 7** | Cache, Session, Celery |

### 7.4 Infrastructure

| Texnologiya | Vazifa |
|-------------|--------|
| **Docker** | Containerization |
| **Docker Compose** | Local development |
| **Nginx** | Reverse proxy, SSL |
| **Hetzner VPS** | Hosting (Germany - EU, O'zbekistonga yaqin) |
| **GitHub Actions** | CI/CD pipeline |
| **Cloudflare** | CDN, DDoS protection |

### 7.5 Development Tools

| Tool | Vazifa |
|------|--------|
| **Ruff** | Linting (flake8 + isort + black replacement) |
| **pytest** | Testing |
| **pytest-django** | Django test utilities |
| **factory_boy** | Test data factories |
| **coverage** | Code coverage |
| **pre-commit** | Git hooks |

### 7.6 requirements/base.txt (Namuna)

```txt
# Core
Django>=5.0,<6.0
djangorestframework>=3.15
psycopg[binary]>=3.1

# Auth
django-allauth>=0.60
djangorestframework-simplejwt>=5.3

# Tasks
celery>=5.4
redis>=5.0

# API
django-filter>=24.0
drf-spectacular>=0.27
django-cors-headers>=4.3

# Production
gunicorn>=22.0
whitenoise>=6.6
sentry-sdk>=1.40

# Utils
python-dotenv>=1.0
Pillow>=10.0
```

### 7.7 requirements/dev.txt (Namuna)

```txt
-r base.txt

# Testing
pytest>=8.0
pytest-django>=4.8
pytest-cov>=4.1
factory_boy>=3.3

# Linting
ruff>=0.2

# Debug
django-debug-toolbar>=4.3
ipython>=8.0
```

### 7.8 Arxitektura Diagrammasi

```
┌─────────────────────────────────────────────────────────────┐
│                        CLOUDFLARE                           │
│                     (CDN + DDoS + SSL)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      HETZNER VPS                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                      NGINX                           │   │
│  │              (Reverse Proxy + Static)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                              │
│              ┌───────────────┼───────────────┐              │
│              ▼               ▼               ▼              │
│  ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │    GUNICORN     │ │   CELERY    │ │   CELERY    │       │
│  │   (Django App)  │ │   WORKER    │ │    BEAT     │       │
│  └─────────────────┘ └─────────────┘ └─────────────┘       │
│              │               │               │              │
│              └───────────────┼───────────────┘              │
│                              ▼                              │
│              ┌───────────────────────────────┐              │
│              │           REDIS               │              │
│              │    (Cache + Celery Broker)    │              │
│              └───────────────────────────────┘              │
│                              │                              │
│                              ▼                              │
│              ┌───────────────────────────────┐              │
│              │        POSTGRESQL             │              │
│              │        (Database)             │              │
│              └───────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Raqobatchi Tahlili: Verifix.uz

> O'zbekistondagi yetakchi HRM tizimi. Tahlil sanasi: 2026-06-09

### Umumiy Ko'rsatkichlar
| Ko'rsatkich | Qiymat |
|------------|--------|
| Foydalanuvchilar | 50,000+ |
| Kompaniyalar | 200+ |
| Mamlakatlar | 5 ta (O'zbekiston, Mongoliya, Xitoy, Kanada...) |
| Qo'llab-quvvatlash | 24/7 |
| Ofis | Toshkent, Maxtumquli 112 |

### Modullar va Funksionallik

| Modul | Funksiya | Daraja |
|-------|----------|--------|
| **Davomat** | Face-ID + Geolokatsiya | Yuqori |
| **Payroll** | Overtim, kasallik, ta'til avtomatik hisoblash | Yuqori |
| **KPI/eKPI** | Samaradorlik kuzatish va baholash | Yuqori |
| **Jadval** | Smenalar, ish grafigi rejalashtirish | O'rta |
| **HR Analytics** | Dashboard, hisobotlar | O'rta |
| **Recruiting** | Ishga qabul jarayoni | Mavjud |
| **Onboarding** | Yangi xodim adaptatsiyasi | Mavjud |
| **Training** | O'qitish va rivojlantirish | Mavjud |
| **Assessment** | Xodimlarni baholash | Mavjud |
| **KDP** | Kadrlar ishi hujjatlari | Mavjud |

### Texnik Xususiyatlar
- **Deployment:** Cloud va On-premise
- **Integratsiya:** CRM, ERP, buxgalteriya tizimlari
- **Soha:** Retail, HoReCa, Logistika, Ishlab chiqarish

### Kuchli Tomonlari
- Face-ID + Geolokatsiya (masofaviy xodimlar uchun ideal)
- To'liq HR jarayonlarini qamrab oladi
- 24/7 texnik qo'llab-quvvatlash
- Enterprise darajadagi yechim

### Kamchiliklari
- Narxlar ochiq emas (demo so'rash kerak)
- API dokumentatsiyasi ochiq emas
- Open-source emas (moslashtirib bo'lmaydi)

### HR-Pro uchun Darslar

| Verifix yondashuvi | HR-Pro alternativasi |
|-------------------|---------------------|
| Face-ID davomat | QR kod yoki PIN (oddiyroq, arzonroq) |
| Geolokatsiya | GPS tracking (ixtiyoriy modul) |
| KPI tizimi | MVP'da oddiy, keyingi versiyalarda kengaytirish |
| Payroll | O'zbekiston soliqlari to'liq hisobga olingan |
| Cloud only | Self-hosted variant ham taklif qilish |

**Manba:** [Verifix.uz](https://verifix.uz/uz/)

---

## 9. O'zbekiston Mehnat Kodeksi - Payroll Formulalari

> Manba: Odoo l10n_uz_hr_payroll moduli (TODOO)
> Audit sanasi: 2026-06-09

### 9.1 Asosiy Ish Haqi Formulasi

```
ISH_HAQI = MHTM × JOB_COEF × LEVEL_COEF × TENURE_COEF
```

| Parametr | Tavsif |
|----------|--------|
| **MHTM** | Mehnatga Haq To'lashning Minimal Miqdori (2025: 1,200,000 so'm) |
| **JOB_COEF** | Lavozim koeffitsiyenti (hr.job.base_coefficient) |
| **LEVEL_COEF** | Daraja koeffitsiyenti (hr.level.growth_coefficient) |
| **TENURE_COEF** | Ish staji koeffitsiyenti (hr.tenure.bracket.coefficient) |

### 9.2 Daraja Tizimi (10 daraja)

| Daraja | Koeffitsiyent | Tavsif |
|--------|---------------|--------|
| Level 1 | 1.00 | Entry-level specialist |
| Level 2 | 1.10 | Junior specialist |
| Level 3 | 1.20 | Mid-level specialist |
| Level 4 | 1.30 | Independent specialist |
| Level 5 | 1.40 | Experienced specialist |
| Level 6 | 1.55 | Highly qualified specialist |
| Level 7 | 1.70 | Senior specialist |
| Level 8 | 1.85 | Lead specialist |
| Level 9 | 2.00 | Principal lead specialist |
| Level 10 | 2.20 | Chief / Lead specialist |

### 9.3 Ish Staji Koeffitsiyentlari

| Staj | Koeffitsiyent |
|------|---------------|
| 0-6 oy | 1.00 |
| 6 oy - 1 yil | 1.10 |
| 1-3 yil | 1.20 |
| 3-6 yil | 1.30 |
| 6+ yil | 1.40 |

**Formula:**
```python
tenure_years = prior_experience + (today - first_contract_date) / 365.25 - unpaid_leave_days / 365.25
```

---

## 10. O'zbekiston Soliq Parametrlari (Qonunchilik)

### 10.1 Asosiy Soliq Stavkalari

| Soliq | Kod | Stavka | Izoh |
|-------|-----|--------|------|
| JSHDT (Daromad solig'i) | `l10n_uz_tax_rate` | **12%** | Jismoniy shaxslardan |
| JSHDT (IT Park) | `l10n_uz_tax_rate_it_park` | **7.5%** | IT Park rezidentlari |
| INPS (Pensiya fondi) | `l10n_uz_pension_rate` | **0.1%** | Xodimdan ushlanadi |
| Ijtimoiy soliq | `l10n_uz_social_tax_rate` | **12%** | Ish beruvchi to'laydi |
| Ijtimoiy soliq (IT Park) | - | **0%** | IT Park rezidentlari |

### 10.2 Ish Vaqti Parametrlari

| Parametr | Qiymat |
|----------|--------|
| O'rtacha ish kunlari (oylik) | 25.3 kun |
| Kunlik ish soatlari | 8 soat |
| Oylik norma soatlar | 168 soat |
| MHEKM (Eng kam ish haqi) | 1,271,000 so'm |

### 10.3 Kasallik Nafaqasi (VM 314-son, 31.05.2024)

**Oddiy kasallik (24-band):**
| Staj | Koeffitsiyent |
|------|---------------|
| 8 yildan kam | 60% |
| 8 yil va undan ko'p | 80% |

**Ijtimoiy ahamiyatli kasallik (22-band):**
*Sil, onkologiya, OITS, moxov, ruhiy, jinsiy kasalliklar*

| Staj | Koeffitsiyent |
|------|---------------|
| 5 yildan kam | 60% |
| 5-8 yil | 80% |
| 8 yil va undan ko'p | 100% |

### 10.4 Homiladorlik Nafaqasi

| Sug'urta staji | Koeffitsiyent |
|----------------|---------------|
| 10-24 oy | 75% |
| 25-60 oy | 85% |
| 61+ oy | 100% |

**Kunlar:**
- Oddiy tug'ish: **126 kun**
- Qiyin/egizak tug'ish: **140 kun**

### 10.5 VM 796-son (17.12.2025) - 2026-yil 1-iyuldan

| Parametr | Qiymat |
|----------|--------|
| Sug'urta staji minimumi | 6 oy |
| Ish beruvchi to'laydigan kunlar | 5 kun |
| Yillik maksimal kasallik kunlari | 182 kun |
| 77+ kun chegirim boshlanishi | 77 kun |
| O'OIH maksimal multiplikatori | 10 × MHTEKM |

**Kasallik staj koeffitsiyentlari (796-son, 18-band):**
| Staj | Koeffitsiyent |
|------|---------------|
| 6-96 oy | 60% |
| 97+ oy | 80% |

### 10.6 Chegirim Chegaralari (MK 270, 312)

| Turi | Chegara |
|------|---------|
| Default chegirim | 50% × GROSS |
| Aliment/Axloq tuzatish | 70% × GROSS |
| Default jarima | 30% × O'rtacha |
| Ichki tartib jarima | 50% × O'rtacha |

### 10.7 Ishdan Bo'shatish (MK 173, 165)

| Parametr | Qiymat |
|----------|--------|
| Severance (kompensatsiya) | 2 oylik maosh |
| Notice (ogohlantirish) | 2 oy |

---

## 11. Ta'til Turlari (Leave Types)

| Turi | Kod | To'lov % | Allocation |
|------|-----|----------|------------|
| Yillik mehnat ta'tili | UZLVANN | 100% | 21 kun |
| To'lovsiz ta'til | UZLVUNP | 0% | Cheksiz |
| Kasallik varaqasi | UZLVSCK | 80% | Cheksiz |
| Homiladorlik ta'tili | UZLVMAT | 100% | 126/140 kun |
| Qisman to'lanadigan | UZLVPAR | 50% | Cheksiz |

---

## 12. HR Buyruqlar Tizimi (Mehnat Kodeksi)

### 12.1 Buyruq Kategoriyalari

| Kategoriya | Kodlar |
|------------|--------|
| **Ishga qabul** | H01, H02, H03 |
| **O'tkazish** | T08, T09 |
| **Ishdan bo'shatish** | Y10, Y11 |
| **Ta'til/Safar** | A05, A06, A07 |
| **Daraja ko'tarish** | P04 |
| **Premiya** | B61 |
| **Hodimga haq** | C71 |

### 12.2 Ishga Qabul Buyruqlari

| Kod | Nomi | MK Moddasi |
|-----|------|------------|
| H01 | Nomuayyan muddatga ishga qabul | 127 |
| H02 | Muayyan muddatga ishga qabul | 127, 492 |
| H03 | Sinov muddati bilan ishga qabul | 127, 130 |

### 12.3 Ishdan Bo'shatish Buyruqlari

| Kod | Nomi | MK Moddasi |
|-----|------|------------|
| Y10 | Taraflar kelishuvi | 157, 171, 172 |
| Y11 | Xodim tashabbusi | 159 |

### 12.4 Ta'til/Safar Buyruqlari

| Kod | Nomi | MK Moddasi |
|-----|------|------------|
| A05 | Yillik mehnat ta'tili | 220 |
| A06 | Xizmat safari | 196 |
| A07 | Kasallik varaqasi | 222 |

---

## 13. Xizmat Safari (Business Trip)

### Buxgalteriya Provodkalari
```
Avans berish:    Dt 4220 / Kr 5110 (Bank) yoki 5530 (Kassa)
Hisobot yopish:  Xodim/kompaniya qarzdorligi balanslash
```

### Xarajatlar Tarkibi
- Sutkalik (ichki/xorij)
- Yo'l haqi
- Turar joy
- Boshqa xarajatlar (cheklar)

---

## 14. Keyingi Tadqiqot Kerak

- [ ] Frontend framework tanlash (React/Vue/HTMX)
- [ ] Hosting platforma (AWS/DigitalOcean/VPS)
- [ ] SMS/Email xabar yuborish servisi
- [ ] Moliya integratsiyasi (1C, bank)
- [x] Raqobatchi tahlili (Verifix) ✓
- [x] Odoo HR/Payroll audit ✓

---

*Oxirgi yangilanish: 2026-06-09*
