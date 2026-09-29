
# 🧠 مشاور — سامانه‌ی جامع مدیریت مرکز مشاوره

> سامانه‌ای فارسی و راست‌چین برای مدیریت کامل مراکز مشاوره و روان‌شناسی: نوبت‌دهی، پرونده مراجعان، جلسات با تایمر زنده، شرح حال محرمانه، مالی، گزارش‌گیری و مدیریت مشاوران.

---

## ✨ قابلیت‌ها

- 🔐 **احراز هویت با کد ملی** — بدون username
- 🛡️ **سه نقش:** مدیر مرکز، مشاور، منشی (با RBAC کامل)
- 💰 **سطوح مشاور با تعرفه‌ی زمانی** — هزینه‌ی دقیقه‌ای مازاد + ارفاق + رُند
- 📅 **برنامه‌ی هفتگی مشاور** + استثناها + مرخصی + شیفت منشی
- ⏱️ **جلسه با تایمر زنده** — شروع / Pause / Resume / پایان + محاسبه‌ی خودکار هزینه
- 🩺 **شرح حال محرمانه** — فقط مشاور و مدیر (منشی دسترسی ندارد)
- 📝 **یادداشت جلسه با ساختار SOAP** — پشتیبانی از صوت و تبدیل به متن
- 💵 **مدیریت مالی** — درآمد، هزینه، نسیه، پرداخت جزئی
- 🔔 **اعلان درون‌برنامه‌ای** — ۷ نوع اعلان
- 🔑 **لایسنس + Trial ۱۴ روزه** — با ۳ لایه ذخیره‌سازی ضدتقلب
- 📊 **گزارش فعالیت‌ها (Audit Log)** — ۱۱ نوع عملیات
- 💾 **پشتیبان‌گیری** + بازیابی
- 🗓️ **تقویم شمسی** + اعداد فارسی در تمام UI
- 🏢 **مدیریت اتاق و حضور روزانه** مشاوران

---

## 🛠️ تکنولوژی‌ها

| لایه | تکنولوژی |
|------|-----------|
| Backend | Django 5.2+ |
| زبان | Python 3.11+ |
| دیتابیس | SQLite (توسعه) / PostgreSQL (تولید) |
| Frontend | Bootstrap 5 RTL |
| فونت | Vazirmatn |
| تاریخ شمسی | jdatetime + persian-datepicker |
| استاتیک | WhiteNoise |
| سرور | Gunicorn |
| تنظیمات محیطی | python-decouple |

> این پروژه از DRF استفاده نمی‌کند. APIها با Django خالص پیاده‌سازی شده‌اند.

---

## 📁 ساختار پروژه
moshaver/
├── config/ # تنظیمات، URLها، WSGI
├── accounts/ # کاربران، نقش‌ها، سطح مشاور، برنامه‌ها
├── appointments/ # نوبت‌ها و مرخصی
├── patients/ # پرونده‌ی مراجعان + شرح حال
├── records/ # جلسات، یادداشت‌ها، محاسبه‌ی هزینه
├── finance/ # تراکنش‌های مالی
├── clinic/ # تنظیمات مرکز، اتاق‌ها، حضور
├── documents/ # مدارک و تصاویر
├── notifications/ # اعلان‌ها
├── licensing/ # لایسنس و Trial
├── audit/ # گزارش فعالیت‌ها
├── backup/ # پشتیبان‌گیری
├── reports/ # گزارش‌های مدیریتی
├── core/ # جست‌وجوی سراسری
├── templates/ # قالب‌های HTML
├── static/ # CSS و JS
├── media/ # فایل‌های آپلودی
├── requirements.txt
├── manage.py
└── .env

text

---

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.11 یا بالاتر
- pip
- Git

### ۱. کلون یا کپی پروژه

```bash
cd D:\projects\moshaver
۲. ساخت محیط مجازی
ویندوز:

bash
python -m venv venv
venv\Scripts\activate
لینوکس / مک:

bash
python3 -m venv venv
source venv/bin/activate
۳. نصب پکیج‌ها
bash
pip install -r requirements.txt
۴. تنظیم فایل .env
bash
copy .env.example .env          # ویندوز
cp .env.example .env            # لینوکس/مک
محتوای حداقلی .env:

env
SECRET_KEY=یک-کلید-تصادفی-بلند-حداقل-۵۰-کاراکتر
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# برای توسعه — SQLite
USE_POSTGRES=False
۵. مهاجرت دیتابیس
bash
python manage.py makemigrations
python manage.py migrate
۶. ساخت کاربر مدیر
bash
python manage.py createsuperuser
کد ملی (به‌جای نام کاربری)

نام و نام خانوادگی

رمز عبور

نقش خودکار: manager

۷. اجرا
bash
python manage.py runserver
سپس در مرورگر باز کن:

👉 http://127.0.0.1:8000

🔑 ورود به سیستم
نقش	دسترسی‌ها
مدیر مرکز	همه‌چیز
مشاور	جلسات خودش، شرح حال مراجعین خودش، برنامه‌ی خودش
منشی	نوبت‌دهی، مالی، تایمر جلسه — بدون دسترسی به شرح حال
ورود با کد ملی + رمز عبور (بدون username).

⚙️ تنظیمات مهم
متغیرهای .env
متغیر	پیش‌فرض	توضیح
SECRET_KEY	—	اجباری در تولید
DEBUG	True	در تولید False
ALLOWED_HOSTS	127.0.0.1,localhost	دامنه‌ها
USE_POSTGRES	False	در تولید True
DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT	—	تنظیمات Postgres
CSRF_TRUSTED_ORIGINS	—	فقط در تولید
SECURE_SSL_REDIRECT	True	در تولید
📝 دستورات مفید
bash
# اجرای سرور توسعه
python manage.py runserver

# ساخت مهاجرت بعد از تغییر مدل
python manage.py makemigrations
python manage.py migrate

# ساخت کاربر مدیر
python manage.py createsuperuser

# جمع‌آوری فایل‌های استاتیک (برای تولید)
python manage.py collectstatic --noinput

# بررسی تنظیمات امنیتی
python manage.py check --deploy
🧪 تست
فعلاً تست‌های خودکار نوشته نشده‌اند. این در Roadmap پروژه قرار دارد.

🚢 استقرار در Production
۱. تنظیم .env
env
SECRET_KEY=کلید-تصادفی-بلند
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
USE_POSTGRES=True
DB_NAME=moshaver
DB_USER=moshaver_user
DB_PASSWORD=رمز-قوی
DB_HOST=localhost
DB_PORT=5432
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
SECURE_SSL_REDIRECT=True
۲. اجرای گام‌ها
bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py check --deploy

gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
📚 مستندات بیشتر
PROJECT_HANDBOOK.md — راهنمای کامل پروژه (معماری، مدل‌ها، الگوها)

AI_CONTEXT.md — سند مخصوص هوش مصنوعی برای درک سریع پروژه

🗺️ Roadmap
☑ فاز ۱ — احراز هویت، RBAC، لایسنس، Audit
☑ فاز ۲ — services برنامه‌ریزی مشاور
☑ فاز ۳ — سطح مشاور، تقویم شمسی، اعداد فارسی
☑ فاز ۴ — جلسات، تایمر، پرداخت، نسیه
☑ فاز ۵ — مراجع، جلسات، API، تقویم
☑ ماژول اعلان‌ها
□ اصلاحات پس از انشعاب از «طبیب»
□ خروجی PDF گزارش‌ها
□ پیامک (SMS)
□ درگاه پرداخت
□ پرسش‌نامه‌های روانشناسی (PHQ-9، GAD-7)
□ نوبت‌دهی آنلاین مراجع
□ اپلیکیشن موبایل
□ تست‌های خودکار
📄 لایسنس
این پروژه خصوصی است. تمام حقوق محفوظ است.

📞 پشتیبانی
برای گزارش باگ یا درخواست قابلیت جدید، از بخش Issues مخزن گیت‌هاب استفاده کنید:

👉 github.com/aliekos007-cloud/moshaver

text

---

## 🎯 دستورات نهایی

```bash
# در پوشه پروژه
notepad README.md
# محتوای بالا را پیست کن، ذخیره کن

git add README.md
git commit -m "docs: افزودن README ساده با راهنمای نصب و اجرا"
git push origin master