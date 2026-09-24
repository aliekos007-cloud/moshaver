# 📘 راهنمای جامع پروژه «طبیب»

> این سند مرجع کامل پروژه است. هر توسعه‌دهنده یا AI که می‌خواهد روی این پروژه کار کند، باید ابتدا این سند را بخواند.

---

## ۱. معرفی پروژه

### 🎯 هدف
سامانه‌ی جامع مدیریت مطب، پرونده الکترونیک مراجع، نسخه‌نویسی، درمان، مالی، انبار، نوبت‌دهی و گزارش‌گیری — کاملاً فارسی و راست‌چین.

### 📅 وضعیت
- **نسخه:** 1.0.0
- **تاریخ شروع:** 1405/06/31 (2026/09/22)
- **وضعیت:** کامل — آماده‌ی استقرار
- **تعداد ماژول‌ها:** ۲۲

### 🛠️ تکنولوژی‌ها

| لایه | تکنولوژی | نسخه |
|------|-----------|------|
| Backend | Django | 6.1.1 |
| Python | Python | 3.14.7 |
| Database | SQLite (dev) / PostgreSQL (prod) | - |
| Frontend | HTML5 + CSS3 + Bootstrap RTL | 5.3.3 |
| Font | Vazirmatn | 33.003 |
| Icons | Bootstrap Icons | 1.11.3 |
| Charts | Chart.js | 4.4.1 |
| Persian Date | persian-datepicker | 1.2.0 |
| Jalali Conversion | jdatetime | 6.1.0 |
| Env Management | python-decouple | - |
| Static Files | WhiteNoise | - |

---

## ۲. ساختار پروژه

### 📁 ساختار کلی

```
tabib/
├── config/                  # تنظیمات پروژه
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                # کاربران، احراز هویت، RBAC
├── core/                    # جست‌وجوی سراسری
├── backup/                  # پشتیبان‌گیری
├── audit/                   # گزارش فعالیت‌ها
├── patients/                # پرونده الکترونیک
├── catalog/                 # بانک‌های دارو/غذا/میوه/توصیه/پرهیز/الزامات
├── records/                 # مراجعات و ویزیت‌ها
├── clinic/                  # تنظیمات مطب
├── documents/               # مدارک و تصاویر
├── therapies/               # اعمال یداوی، بازتاب‌درمانی، دیسکوپاتی
├── finance/                 # مالی و تراکنش‌ها
├── inventory/               # انبار
├── consent/                 # رضایت‌نامه
├── reports/                 # گزارش‌های مدیریتی
├── licensing/               # لایسنس و Trial
├── appointments/            # نوبت‌دهی و برنامه هفتگی
├── templates/               # قالب‌های HTML
│   ├── base.html            # ★ قالب اصلی
│   ├── dashboard.html
│   ├── registration/
│   ├── patients/
│   ├── accounts/
│   ├── catalog/
│   ├── records/
│   ├── clinic/
│   ├── documents/
│   ├── therapies/
│   ├── finance/
│   ├── inventory/
│   ├── consent/
│   ├── reports/
│   ├── licensing/
│   └── appointments/
├── media/                   # فایل‌های آپلودی
├── staticfiles/             # فایل‌های static (production)
├── backups/                 # پشتیبان‌ها
├── logs/                    # لاگ‌ها
├── scripts/                 # اسکریپت‌های کمکی
├── venv/                    # محیط مجازی
├── manage.py
├── requirements.txt
├── .env                     # ★ تنظیمات محلی (در Git نباشد)
├── .env.example             # نمونه
└── db.sqlite3               # دیتابیس dev
```

### 📦 لیست اپ‌ها (۲۲ اپ)

| # | اپ | مسئولیت |
|---|-----|---------|
| ۱ | `accounts` | کاربر، نقش‌ها، ورود/خروج، مدیریت کاربران |
| ۲ | `core` | جست‌وجوی سراسری |
| ۳ | `backup` | پشتیبان‌گیری و بازیابی |
| ۴ | `audit` | ثبت تمام فعالیت‌ها |
| ۵ | `patients` | پرونده الکترونیک مراجع |
| ۶ | `catalog` | ۶ بانک اطلاعاتی (دارو، غذا، میوه، توصیه، پرهیز، الزامات) |
| ۷ | `records` | مراجعات، نسخه، دارو‌های تجویزی |
| ۸ | `clinic` | تنظیمات مطب (Singleton) |
| ۹ | `documents` | آرشیو تصاویر و مدارک |
| ۱۰ | `therapies` | اعمال یداوی، بازتاب‌درمانی، دیسکوپاتی |
| ۱۱ | `finance` | تراکنش‌های مالی |
| ۱۲ | `inventory` | انبار |
| ۱۳ | `consent` | رضایت‌نامه |
| ۱۴ | `reports` | گزارش‌های مدیریتی |
| ۱۵ | `licensing` | لایسنس و Trial |
| ۱۶ | `appointments` | نوبت‌دهی، برنامه هفتگی، مرخصی |

---

## ۳. الگوهای معماری

### 🔐 ۱) احراز هویت با کد ملی

`AUTH_USER_MODEL = "accounts.User"` با `USERNAME_FIELD = "national_code"`.

**نقش‌ها:**
- `manager` — مدیر مطب (همه دسترسی)
- `physician` — طبیب
- `secretary` — منشی

### 🛡️ ۲) RBAC (کنترل دسترسی مبتنی بر نقش)

**فایل‌های کلیدی:**
- `accounts/permissions.py` — توابع `is_manager()`, `can_view_medical()`, ...
- `accounts/decorators.py` — دکوراتورهای `manager_required`, `medical_view_required`, ...
- `accounts/templatetags/role_tags.py` — فیلترهای قالب

**الگوی استفاده در view:**
```python
@medical_edit_required
def patient_create(request): ...
```

**الگوی استفاده در template:**
```django
{% if user|can_edit_medical %}...{% endif %}
```

### 📋 ۳) Audit Log

**فایل کلیدی:** `audit/models.py` → تابع `log_action()`

**الگوی استفاده:**
```python
from audit.models import log_action

log_action(request, "create", obj, description="توضیحات")
log_action(request, "update", obj)
log_action(request, "delete", obj)
log_action(request, "print", obj)
```

**نکته مهم:** دکوراتور `login_required` + ثبت خودکار ورود/خروج با signal.

### 🔑 ۴) Licensing + Trial ۱۴ روزه

**فایل‌های کلیدی:**
- `licensing/models.py` — مدل‌های `License` و `TrialState`
- `licensing/services.py` — ذخیره‌سازی ۳ لایه (DB + File + Registry)
- `licensing/middleware.py` — قفل سامانه بعد از انقضا
- `licensing/decorators.py` — `feature_required("inventory")`

**الگوی محافظت از ماژول:**
```python
@feature_required("inventory")
@medical_view_required
def inventory_dashboard(request): ...
```

**الگوی پنهان کردن در سایدبار:**
```django
{% if user|has_feature:"inventory" %}
<a href="...">انبار</a>
{% endif %}
```

**ویژگی‌های لایسنس:**
- `enable_inventory`, `enable_finance`, `enable_therapies`, `enable_documents`,
  `enable_consent`, `enable_reports`, `enable_backup`, `enable_audit`, `enable_appointments`

### 📅 ۵) تاریخ شمسی

**فایل کلیدی:** `accounts/templatetags/jalali_tags.py`

**فیلترها:**
| فیلتر | مثال |
|-------|------|
| `jalali` | `1405/07/01` |
| `jalali_datetime` | `1405/07/01 — 14:30` |
| `jalali_full` | `۱ مهر ۱۴۰۵` |
| `jalali_short` | `۱ مهر` |
| `jalali_time` | `14:30` |

**نکته مهم:** `USE_TZ = True` + تبدیل `timezone.localtime()`.

### 🎨 ۶) رابط کاربری

**قالب اصلی:** `templates/base.html`

**ویژگی‌ها:**
- راست‌چین کامل (`dir="rtl"`)
- فونت Vazirmatn
- سایدبار تیره ثابت (دسکتاپ) + کشویی (موبایل)
- Toast Notification (به‌جای Alert)
- کارت‌های آماری (`.stat-card`)
- جدول‌های واکنش‌گرا (`.table-responsive-stack`)

**پالت رنگی:**
```css
--primary: #2563eb;      /* آبی */
--secondary: #06b6d4;    /* فیروزه‌ای */
--success: #10b981;      /* سبز */
--danger: #ef4444;       /* قرمز */
--warning: #f59e0b;      /* نارنجی */
```

**جاوااسکریپت‌های مهم:**
- `toggleSidebar()` — باز/بستن منوی موبایل
- `showToast(text, tags)` — نمایش Toast
- `Ctrl+K` — فوکوس روی جست‌وجو

### 🗓️ ۷) تقویم شمسی در فرم‌ها

**الگوی استفاده:**

```django
{% block extra_css %}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/persian-datepicker@1.2.0/dist/css/persian-datepicker.min.css">
{% endblock %}

<!-- در فرم -->
<input type="text" id="date_display" class="form-control" readonly>
{{ form.date }}  {# HiddenInput #}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/persian-date@1.1.0/dist/persian-date.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/persian-datepicker@1.2.0/dist/js/persian-datepicker.min.js"></script>
<script>
$("#date_display").persianDatepicker({
    format: 'YYYY/MM/DD',
    altField: '#id_date',
    altFormat: 'YYYY-MM-DD',
    autoClose: true, persianDigit: true,
});
</script>
{% endblock %}
```

---

## ۴. مدل‌های اصلی دیتابیس

### 👤 `accounts.User` (جایگزین `auth.User`)

| فیلد | نوع | توضیح |
|------|------|-------|
| `national_code` | CharField | شناسه یکتا (به‌جای username) |
| `first_name`, `last_name` | CharField | اجباری |
| `role` | CharField | `manager`/`physician`/`secretary` |
| `phone` | CharField | اختیاری |

### 👥 `patients.Patient`

| فیلد | توضیح |
|------|-------|
| `file_number` | خودکار (00001، 00002، ...) |
| `national_code` | اعتبارسنجی الگوریتم ایران + unique |
| `mobile` | اعتبارسنجی ایران |
| `birth_date` | از تقویم شمسی ذخیره می‌شود |

### 📋 `records.Visit`

| فیلد | توضیح |
|------|-------|
| `patient`, `physician` | FK |
| `prescription_serial` | خودکار (RX-1405-00001) |
| `chief_complaint`, `history`, `diagnosis`, ... | بالینی |

**جدول‌های وابسته:**
- `PrescriptionItem` (داروها)
- `VisitFood`, `VisitFruit`
- `VisitRecommendation`, `VisitAvoidance`, `VisitNutrition`

### 📚 `catalog` (۶ مدل)

`Medicine`, `Food`, `Fruit`, `Recommendation`, `Avoidance`, `NutritionRequirement`

### 💰 `finance.Transaction`

| فیلد | توضیح |
|------|-------|
| `receipt_number` | خودکار (RC-1405-00001 یا PY-1405-00001) |
| `transaction_type` | `income`/`expense` |
| `category` | ۱۰ دسته |
| `amount` | Decimal |

### 📦 `inventory`

- `Item` — کالا
- `StockEntry` — ورود
- `StockExit` — خروج

`Item.current_stock` محاسبه‌ی داینامیک دارد.

### 📅 `appointments`

- `WeeklySchedule` — برنامه هفتگی
- `TimeOff` — مرخصی
- `Appointment` — نوبت

### 🔑 `licensing`

- `License` — لایسنس
- `TrialState` — وضعیت دوره آزمایشی

### 📋 `audit.AuditLog`

ثبت کامل با ایندکس روی `created_at`, `user`, `action`, `model_name`.

---

## ۵. ایندکس‌های دیتابیس (مهم برای performance)

| جدول | ایندکس | کاربرد |
|------|--------|--------|
| `Patient` | `(last_name, first_name)`, `(mobile)`, `(-created_at)` | جست‌وجو |
| `Visit` | `(patient, -visited_at)`, `(physician, -visited_at)` | تاریخچه |
| `Transaction` | `(-transaction_date)`, `(transaction_type, -transaction_date)` | گزارش مالی |
| `Appointment` | `(date, physician)`, `(date, start_time)` | تقویم |
| `AuditLog` | `(-created_at)`, `(user, -created_at)` | گزارش فعالیت |
| `Item` | `(name)`, `(category, is_active)` | انبار |

---

## ۶. فایل‌های حساس / مهم

| فایل | چرا مهم است |
|------|-----------|
| `config/settings.py` | تمام تنظیمات |
| `templates/base.html` | قالب اصلی همه‌ی صفحات |
| `accounts/permissions.py` | هسته‌ی RBAC |
| `accounts/decorators.py` | دکوراتورهای دسترسی |
| `accounts/templatetags/role_tags.py` | فیلترهای RBAC |
| `accounts/templatetags/jalali_tags.py` | تاریخ شمسی |
| `licensing/services.py` | Trial و ضدتقلب |
| `audit/models.py::log_action` | ثبت فعالیت |
| `config/urls.py` | نقشه‌ی URLها |

---

## ۷. راهنمای نصب و اجرا

### پیش‌نیازها
- Python 3.11+
- pip
- Git (اختیاری)

### گام‌های نصب

```bash
# ۱. کلون یا کپی پروژه
cd D:\projects\tabib

# ۲. محیط مجازی
python -m venv venv
venv\Scripts\activate          # ویندوز
source venv/bin/activate       # لینوکس/مک

# ۳. نصب پکیج‌ها
pip install -r requirements.txt

# ۴. تنظیمات محیط
copy .env.example .env
# ویرایش .env

# ۵. دیتابیس
python manage.py makemigrations
python manage.py migrate

# ۶. کاربر مدیر
python manage.py createsuperuser
# کد ملی، نام، نام خانوادگی، رمز
# نقش خودکار: manager

# ۷. اجرا
python manage.py runserver
```

### آدرس‌های مهم

| آدرس | کاربرد |
|------|--------|
| `/` | داشبورد |
| `/admin/` | پنل ادمین |
| `/accounts/login/` | ورود |
| `/patients/` | مراجعین |
| `/appointments/` | نوبت‌دهی |
| `/finance/` | مالی |
| `/reports/` | گزارش‌ها |
| `/licensing/` | لایسنس |

---

## ۸. راهنمای استقرار (Production)

### محیط‌های پیشنهادی
- **PaaS ایران:** لیارا، ابرآروان، پارس‌پک
- **PaaS بین‌المللی:** Railway، Render، PythonAnywhere
- **VPS:** Hetzner، DigitalOcean، Liara VPS

### تنظیمات `.env` برای Production

```env
SECRET_KEY=<کلید-تصادفی-بلند-حداقل-۵۰-کاراکتر>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

USE_POSTGRES=True
DB_NAME=tabib
DB_USER=tabib_user
DB_PASSWORD=<رمز-قوی>
DB_HOST=localhost
DB_PORT=5432

CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECURE_SSL_REDIRECT=True
```

### گام‌های استقرار

```bash
# ۱. کپی فایل‌ها روی سرور

# ۲. محیط مجازی + پکیج‌ها
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ۳. تنظیمات
cp .env.example .env
nano .env

# ۴. دیتابیس
python manage.py migrate

# ۵. کاربر مدیر
python manage.py createsuperuser

# ۶. فایل‌های static
python manage.py collectstatic --noinput

# ۷. تست
python manage.py check --deploy

# ۸. اجرا با Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Nginx (اختیاری، برای HTTPS)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/tabib/staticfiles/;
    }

    location /media/ {
        alias /path/to/tabib/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## ۹. تله‌ها و نکات مهم

### ⚠️ ۱) Django 6.1 vs Python 3.14

- Django 5.0 با Python 3.14 کار نمی‌کند → **حتماً Django 5.2+**
- `forms.CharField("label", ...)` دیگر کار نمی‌کند → `forms.CharField(label="label", ...)`

### ⚠️ ۲) jdatetime و timezone

`jdatetime.datetime.fromgregorian()` با timezone-aware کار نمی‌کند.

**راه‌حل:**
```python
from django.utils import timezone
local_naive = timezone.localtime(value).replace(tzinfo=None)
j = jdatetime.datetime.fromgregorian(datetime=local_naive)
```

### ⚠️ ۳) Circular Imports

مشکل رایج: `accounts.views` → `patients.models` → ...

**راه‌حل:** import داخل تابع، نه بالای فایل.

### ⚠️ ۴) Static Files

در `DEBUG=False` فایل‌های static سرو نمی‌شوند. **حتماً:**
- `whitenoise` در `MIDDLEWARE`
- `python manage.py collectstatic`

### ⚠️ ۵) همه‌ی `{% if %}`ها باید بسته شوند

`base.html` بسیار بزرگ است. اگه خطای `Unclosed tag` دیدی، یک `{% endif %}` جا افتاده.

### ⚠️ ۶) `feature_required` قبل از `medical_view_required`

```python
@feature_required("inventory")   # ✅ اول
@medical_view_required
def ...
```

### ⚠️ ۷) محاسبه‌ی `file_number`

در `Patient.save()` — دو بار save می‌شود (یک بار برای pk، یک بار برای file_number).

---

## ۱۰. کارهای آینده (Roadmap)

### ✅ تکمیل‌شده
- تمام ۲۲ ماژول بالا

### 🟡 در حال توسعه
- بهینه‌سازی برای مراکز مشاوره (تعرفه‌ی زمانی، چند روانشناس همزمان)

### 🔴 باقی‌مانده
- [ ] صندوق روزانه (فصل ۲۰ RFP)
- [ ] خروجی PDF گزارش‌ها
- [ ] داشبورد پیشرفته
- [ ] پیامک (SMS)
- [ ] درگاه پرداخت
- [ ] پرسش‌نامه‌های استاندارد روانشناسی (PHQ-9، GAD-7)
- [ ] نوبت‌دهی آنلاین برای مراجع
- [ ] اپلیکیشن موبایل (Flutter + DRF)

---

## ۱۱. الگوهای کدنویسی پروژه

### ساختار view استاندارد

```python
@feature_required("module_name")
@permission_decorator
def view_name(request, ...):
    # ۱. خواندن داده
    # ۲. پردازش (POST)
    # ۳. ثبت Audit
    # ۴. پیام موفقیت
    # ۵. redirect یا render
```

### ساختار فرم استاندارد

```python
class MyForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = (...)
        widgets = {...}
    
    def __init__(self, *args, **kwargs):
        patient = kwargs.pop("patient", None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # اعمال کلاس‌های CSS
        # مقادیر اولیه
```

### ساختار قالب استاندارد

```django
{% extends "base.html" %}
{% load jalali_tags %}
{% block title %}عنوان{% endblock %}
{% block header %}<i class="bi bi-icon"></i> عنوان{% endblock %}
{% block subtitle %}<div class="page-subtitle">زیرعنوان</div>{% endblock %}
{% block topbar_actions %}
    <a href="..." class="btn btn-primary">دکمه</a>
{% endblock %}
{% block content %}
    <div class="card">...</div>
{% endblock %}
```

---

## ۱۲. تماس و اطلاعات

**پروژه:** طبیب — سامانه جامع طبابت و درمان
**توسعه:** جلسات همکاری با AI
**شروع:** 1405/06/31
**نسخه:** 1.0.0

---

## 📌 پایان

این سند به‌روز است تا تاریخ **1405/07/01**.

هر توسعه‌دهنده‌ی جدید (انسان یا AI) باید:
1. این سند را کامل بخواند
2. `config/settings.py` را ببیند
3. `templates/base.html` را ببیند
4. یک نگاه به `config/urls.py` بیندازد

سپس می‌تواند با اطمینان کار کند.