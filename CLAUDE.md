# HR-Pro Loyihasi Qoidalari

> **MUHIM:** Bu loyiha professional darajada bo'lishi kerak.
> Har bir qadam aniq, xatosiz, dokumentatsiya bilan.

---

## 0. LOYIHA KONTEKSTI (HAR DOIM ESDA TUT)

```
LOYIHA: HR-Pro (Human Resources & Payroll Management System)
MAMLAKAT: O'zbekiston
QONUNCHILIK: Mehnat Kodeksi, Soliq Kodeksi
STACK: Django 5 + HTMX + Tailwind + PostgreSQL + DRF (API)
```

### Asosiy Fayllar (Chalkashmaslik uchun):
| Fayl | Vazifa |
|------|--------|
| `CLAUDE.md` | Qoidalar (SHU FAYL) |
| `KNOWLEDGE.md` | Texnik bilimlar bazasi |
| `docs/ARCHITECTURE.md` | Arxitektura qarorlari |
| `docs/API.md` | API dokumentatsiya |
| `docs/CHANGELOG.md` | O'zgarishlar tarixi |

### Har Safar Kod Yozishdan OLDIN:
1. **KNOWLEDGE.md** ni tekshir - formula/qoida bormi?
2. **Mavjud kod** ni o'qi - pattern qanday?
3. **KEYIN** yoz

---

## 1. ASOSIY QOIDA: TAXMIN QILMA

```
┌─────────────────────────────────────────┐
│  TAXMIN QILMA = AVVAL O'QI, KEYIN YOZ   │
│                                          │
│  ❌ "Bu field bor deb o'ylayman"         │
│  ✅ "Model faylini o'qib, field borligini│
│      tasdiqladim"                        │
└─────────────────────────────────────────┘
```

### Kod Yozishdan OLDIN Checklist:
- [ ] Model/fayl mavjudmi? → `Read` tool bilan tekshir
- [ ] Field nomlari aniqmi? → Model faylini o'qi
- [ ] Import path to'g'rimi? → Fayl strukturasini ko'r
- [ ] Formula to'g'rimi? → KNOWLEDGE.md da bor

### QILMA:
- Field nomini taxmin qilish
- Mavjud bo'lmagan method chaqirish
- "Ehtimol...", "Shunday bo'lishi kerak..." deb kod yozish
- O'qimay taklif berish

---

## 2. LOYIHA STRUKTURASI (Aniq Qoida)

```
hr-pro/
├── config/                     # Django settings
│   ├── settings/
│   │   ├── base.py            # Umumiy settings
│   │   ├── dev.py             # Development
│   │   └── prod.py            # Production
│   ├── urls.py                # Root URLs
│   └── wsgi.py
│
├── apps/                       # Django apps
│   ├── core/                  # Umumiy utilities
│   │   ├── models.py          # BaseModel (abstract)
│   │   ├── mixins.py          # View mixins
│   │   └── utils.py           # Helper functions
│   │
│   ├── accounts/              # Foydalanuvchilar
│   │   ├── models.py          # User, Profile
│   │   ├── views.py           # Login, Register
│   │   ├── api/               # DRF endpoints
│   │   └── templates/
│   │
│   ├── employees/             # Xodimlar
│   │   ├── models.py          # Employee, Department, Position
│   │   ├── services.py        # Business logic
│   │   ├── views.py           # HTMX views
│   │   ├── api/               # DRF endpoints
│   │   └── templates/
│   │
│   ├── attendance/            # Davomat
│   ├── leave/                 # Ta'tillar
│   ├── payroll/               # Ish haqi
│   │   ├── models.py          # Payroll, PayrollItem
│   │   ├── services.py        # Hisoblash formulalari
│   │   ├── calculations.py    # Soliq, INPS, JSHDT
│   │   └── ...
│   │
│   ├── orders/                # HR Buyruqlar
│   └── reports/               # Hisobotlar
│
├── templates/                  # Global templates
│   ├── base.html
│   ├── components/            # HTMX components
│   └── includes/              # Partials
│
├── static/                     # Static files
├── tests/                      # Test files
├── docs/                       # Documentation
├── requirements/               # Dependencies
├── docker/                     # Docker files
├── CLAUDE.md                   # Qoidalar
└── KNOWLEDGE.md                # Bilimlar bazasi
```

### Yangi App Yaratish Qoidasi:
```bash
# 1. App yaratish
python manage.py startapp app_name apps/app_name

# 2. apps.py ni yangilash
class AppNameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.app_name'  # TO'LIQ PATH

# 3. INSTALLED_APPS ga qo'shish
'apps.app_name',
```

---

## 3. NAMING CONVENTIONS (Aniq Qoida)

### Python/Django:
| Nima | Format | Misol |
|------|--------|-------|
| Model | `PascalCase` | `Employee`, `LeaveRequest` |
| Field | `snake_case` | `first_name`, `hire_date` |
| Method | `snake_case` | `calculate_salary()` |
| Constant | `UPPER_SNAKE` | `MAX_LEAVE_DAYS` |
| File | `snake_case` | `employee_service.py` |

### URLs:
| Turi | Format | Misol |
|------|--------|-------|
| Web UI | `kebab-case` | `/employees/`, `/leave-requests/` |
| API | `kebab-case` | `/api/v1/employees/` |
| HTMX partial | `_` prefix | `/_partials/employee-row/` |

### Templates:
| Turi | Format | Misol |
|------|--------|-------|
| Full page | `snake_case.html` | `employee_list.html` |
| Partial | `_prefix.html` | `_employee_row.html` |
| Component | `components/` | `components/modal.html` |

---

## 4. MODEL YOZISH QOIDASI

### Har Bir Model Uchun:
```python
from apps.core.models import BaseModel

class Employee(BaseModel):
    """
    Xodim modeli.

    Bog'liqliklar:
        - Department (ForeignKey)
        - Position (ForeignKey)
        - User (OneToOne, optional)

    Formulalar:
        - Ish haqi: KNOWLEDGE.md 9.1-bo'lim
    """

    class Meta:
        verbose_name = "Xodim"
        verbose_name_plural = "Xodimlar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee_code']),
            models.Index(fields=['department', 'status']),
        ]
```

### BaseModel (Har bir modelda bo'ladi):
```python
class BaseModel(models.Model):
    """Abstract base model."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

---

## 5. SERVICE LAYER (Business Logic)

### Qoida: View'da business logic YOZMA

```python
# ❌ NOTO'G'RI - View'da hisoblash
class PayrollView(View):
    def post(self, request):
        salary = employee.base_salary * 1.2 - tax  # YOMON!

# ✅ TO'G'RI - Service'da hisoblash
# services.py
class PayrollService:
    def calculate_salary(self, employee, period):
        """
        Ish haqi hisoblash.
        Formula: KNOWLEDGE.md 9.1-bo'lim
        """
        ...

# views.py
class PayrollView(View):
    def post(self, request):
        salary = PayrollService().calculate_salary(employee, period)
```

---

## 6. HTMX QOIDALARI

### Partial Template Nomi:
```
_<action>_<element>.html

Misollar:
_employee_row.html      # Bitta qator
_employee_list.html     # Ro'yxat
_employee_form.html     # Forma
_employee_modal.html    # Modal
```

### HTMX View Pattern:
```python
def employee_row(request, pk):
    """HTMX partial: bitta xodim qatori."""
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/_employee_row.html', {
        'employee': employee
    })
```

---

## 7. API QOIDALARI (DRF)

### Versiyalash:
```
/api/v1/employees/     # Version 1
/api/v2/employees/     # Version 2 (kelajakda)
```

### Response Format:
```json
{
    "success": true,
    "data": { ... },
    "message": "Success",
    "errors": null
}
```

### Error Response:
```json
{
    "success": false,
    "data": null,
    "message": "Validation error",
    "errors": {
        "email": ["Bu email allaqachon mavjud"]
    }
}
```

---

## 8. TEST QOIDALARI

### Test Yozishdan OLDIN:
1. Model faylini **O'QI**
2. Qaysi fieldlar borligini **ANIQLA**
3. KNOWLEDGE.md da formula **TEKSHIR**
4. **KEYIN** test yoz

### Test Fayl Strukturasi:
```
tests/
├── conftest.py              # Fixtures
├── factories.py             # Factory Boy
├── test_models/
│   ├── test_employee.py
│   └── test_payroll.py
├── test_services/
│   └── test_payroll_service.py
├── test_views/
│   └── test_employee_views.py
└── test_api/
    └── test_employee_api.py
```

### Test Pattern:
```python
class TestPayrollCalculation:
    """
    Ish haqi hisoblash testlari.
    Formula: KNOWLEDGE.md 9.1-bo'lim
    """

    def test_basic_salary_calculation(self, employee_factory):
        # Arrange
        employee = employee_factory(level=3, job_coefficient=1.5)

        # Act
        result = PayrollService().calculate_salary(employee)

        # Assert
        # MHTM(1,200,000) × JOB(1.5) × LEVEL(1.2) × TENURE(1.0)
        expected = 1_200_000 * 1.5 * 1.2 * 1.0
        assert result == expected
```

---

## 9. GIT QOIDALARI

### Branch Nomi:
```
feature/EMP-001-add-employee-crud
bugfix/PAY-002-fix-tax-calculation
hotfix/SEC-003-fix-auth-vulnerability
```

### Commit Message:
```
feat(employees): add CRUD endpoints

- Add Employee model with all fields
- Add EmployeeService for business logic
- Add list/create/update/delete views
- Add tests for all operations

Refs: EMP-001
```

### QILMA:
- `.env`, secrets commit qilish
- Force push (`--force`)
- `main` ga to'g'ridan push
- Test yozmay commit qilish

---

## 10. XAVFSIZLIK QOIDALARI

| Qoida | Bajarish |
|-------|----------|
| Secrets | `.env` faylda, HECH QACHON kod ichida |
| SQL | Raw SQL YOZMA, ORM ishlatish |
| XSS | Template'da `{{ var }}` (auto-escape) |
| CSRF | Form'larda `{% csrf_token %}` |
| Auth | `@login_required` yoki `LoginRequiredMixin` |
| Input | Serializer/Form bilan validate |

---

## 11. DOKUMENTATSIYA QOIDASI

### Har Bir Yangi Feature Uchun:
1. **KNOWLEDGE.md** yangilash (formula, qoida bo'lsa)
2. **Docstring** yozish (model, service, view)
3. **CHANGELOG.md** yangilash

### Docstring Format:
```python
def calculate_salary(self, employee: Employee, period: date) -> Decimal:
    """
    Xodim ish haqini hisoblash.

    Formula: MHTM × JOB_COEF × LEVEL_COEF × TENURE_COEF
    Manba: KNOWLEDGE.md 9.1-bo'lim

    Args:
        employee: Xodim obyekti
        period: Hisoblash davri (oy boshi)

    Returns:
        Decimal: Hisoblangan ish haqi (so'm)

    Raises:
        ValueError: MHTM topilmasa
    """
```

---

## 12. O'ZGARISHLARNI TRACK QILISH

### Har Bir Sessiya Oxirida:
1. Nima qilindi - qisqacha
2. KNOWLEDGE.md yangilandimi?
3. Keyingi qadam nima?

### Progress Tracking:
```
docs/PROGRESS.md - Loyiha progressi
docs/TODO.md - Bajarilishi kerak ishlar
```

---

## 13. TIL QOIDALARI

| Nima | Til |
|------|-----|
| Javoblar | O'zbekcha |
| Kod comments | O'zbekcha (qisqa) |
| Docstring | English |
| Commit message | English |
| Variable nomi | English |
| UI text | O'zbekcha |
| Error messages | O'zbekcha |

---

## 14. CHALKASHMASLIK UCHUN

### Loyiha Kattalashganda:
1. **KNOWLEDGE.md** - formula/qoida kerakmi? SHU YERDA
2. **Fayl strukturasi** - bu CLAUDE.md 2-bo'lim
3. **Naming** - bu CLAUDE.md 3-bo'lim
4. **Pattern** - mavjud kodni o'qi

### Yangi Narsa Qo'shishdan OLDIN:
```
1. KNOWLEDGE.md tekshir
2. Mavjud pattern o'qi
3. To'g'ri joyga qo'sh
4. Dokumentatsiya yoz
5. Test yoz
```

---

*Oxirgi yangilanish: 2026-06-09*
*Versiya: 2.0 (Professional Edition)*
