فایل نهایی ۱: PROJECT_HANDBOOK.md
markdown
# 📘 راهنمای جامع پروژه «مشاور»

> این سند مرجع کامل پروژه است. هر توسعه‌دهنده یا AI که می‌خواهد روی این پروژه کار کند، باید ابتدا این سند را بخواند.

---

## ۱. معرفی پروژه

### 🎯 هدف
سامانه‌ی جامع مدیریت مرکز مشاوره — نوبت‌دهی، پرونده مراجعان، جلسات مشاوره (با تایمر زنده و Pause)، شرح حال محرمانه، مالی، گزارش‌گیری، لایسنس و Trial، اعلان‌ها و مدیریت کاربران — کاملاً فارسی و راست‌چین.

### 📅 وضعیت
- **نسخه:** 1.0.0
- **وضعیت:** فاز ۵ تکمیل، فاز اصلاحات در جریان
- **تعداد اپ‌ها:** ۱۳ اپ فعال
- **منشأ:** منشعب از پروژه «طبیب» (سامانه مدیریت مطب) — بازنویسی و بازطراحی برای مراکز مشاوره

### 🛠️ تکنولوژی‌ها

| لایه | تکنولوژی | نسخه |
|------|-----------|------|
| Backend | Django | 5.2+ (< 7.0) |
| Python | Python | 3.11+ |
| Database | SQLite (dev) / PostgreSQL (prod) | — |
| Frontend | HTML5 + CSS3 + Bootstrap RTL | 5.3.3 |
| Font | Vazirmatn | 33.003 |
| Icons | Bootstrap Icons | 1.11.3 |
| Persian Date | persian-datepicker | 1.2.0 |
| Jalali Conversion | jdatetime | 6.1.0 |
| Env Management | python-decouple | — |
| Static Files | WhiteNoise | — |
| Image | Pillow | — |
| WSGI Server | Gunicorn | 22.0.0 |
| PostgreSQL Driver | psycopg[binary] | 3.1.0+ |

**نکته مهم:** از **DRF استفاده نمی‌شود**. APIها با `JsonResponse` (Django خالص) پیاده‌سازی شده‌اند.

---

## ۲. ساختار پروژه

### 📁 ساختار کلی
moshaver/
├── config/ # تنظیمات پروژه
│ ├── settings.py
│ ├── urls.py # ★ نقشه URL اصلی
│ ├── wsgi.py
│ └── asgi.py
├── accounts/ # کاربران، RBAC، سطح مشاور، برنامه‌ها
│ ├── views/
│ │ ├── init.py # re-export همه views
│ │ └── consultants/ # ★ پکیج ویوهای مشاوران
│ │ ├── init.py
│ │ ├── levels.py # CRUD سطح مشاور
│ │ ├── schedule.py # برنامه هفتگی/ماهانه
│ │ ├── exceptions.py # مرخصی و استثناها
│ │ ├── api.py # API ذخیره/ریست روز
│ │ └── search.py # جست‌وجوی اسلات
│ ├── templatetags/
│ │ ├── jalali_tags.py # فیلترهای تاریخ شمسی
│ │ ├── persian_numbers.py # اعداد فارسی
│ │ └── role_tags.py # فیلترهای RBAC
│ ├── permissions.py # توابع دسترسی
│ ├── decorators.py # دکوراتورهای RBAC
│ ├── urls.py
│ └── models.py
├── appointments/ # Appointment، TimeOff، WeeklySchedule (legacy)
│ └── models.py
├── notifications/ # اعلان‌ها
├── audit/ # AuditLog + log_action()
├── backup/ # BackupRecord
├── clinic/ # ClinicSettings, Room, Presence, RoomChange
├── core/ # جست‌وجوی سراسری (بدون مدل)
├── documents/ # مدارک (مدل‌ها دیده نشده)
├── finance/ # Transaction
├── licensing/ # License, TrialState, middleware, services
│ ├── fingerprint.py
│ ├── services.py
│ ├── middleware.py
│ ├── decorators.py
│ ├── context_processors.py
│ └── templatetags/
│ └── license_tags.py
├── patients/ # Patient, ClientNarrative
├── records/ # Visit (legacy), Session, SessionNote, SessionNoteRevision
├── reports/ # بدون مدل
├── templates/
│ ├── base.html # ★ قالب اصلی
│ ├── registration/login.html
│ ├── licensing/
│ │ ├── expired.html
│ │ └── feature_disabled.html
│ └── ...
├── static/
│ ├── css/{base.css, modals.css}
│ └── js/{base.js, modals.js, jalali-datepicker.js}
├── media/
├── staticfiles/
├── logs/
├── backups/
├── manage.py
├── requirements.txt
├── .env
└── db.sqlite3

text

### 📦 لیست اپ‌ها (۱۳ اپ)

| # | اپ | مسئولیت | مدل‌ها |
|---|-----|---------|---------|
| ۱ | `accounts` | کاربر، RBAC، سطح مشاور، برنامه، شیفت منشی | User, ConsultantLevel, ConsultantWeeklySchedule, ConsultantScheduleOverride, ConsultantSlotSettings, ScheduleChangeLog, SecretaryShift |
| ۲ | `appointments` | نوبت و مرخصی | Appointment, TimeOff, WeeklySchedule (legacy) |
| ۳ | `patients` | مراجعان و شرح حال | Patient, ClientNarrative |
| ۴ | `records` | جلسات و یادداشت | Visit (legacy), Session, SessionNote, SessionNoteRevision |
| ۵ | `finance` | مالی | Transaction |
| ۶ | `clinic` | تنظیمات، اتاق، حضور | ClinicSettings, Room, ConsultantDailyPresence, ConsultantRoomChange |
| ۷ | `notifications` | اعلان‌ها | Notification |
| ۸ | `licensing` | لایسنس و Trial | License, TrialState |
| ۹ | `audit` | گزارش فعالیت | AuditLog |
| ۱۰ | `backup` | پشتیبان | BackupRecord |
| ۱۱ | `documents` | مدارک | (مدل‌ها دیده نشده) |
| ۱۲ | `reports` | گزارش‌ها | بدون مدل |
| ۱۳ | `core` | جست‌وجو | بدون مدل |

---

## ۳. نقشه‌ی URLها (`config/urls.py`)

| مسیر | اپ | توضیح |
|------|-----|-------|
| `/admin/` | Django admin | پنل ادمین |
| `/accounts/` | accounts | ورود، مشاوران، سطوح، برنامه‌ها، جست‌وجوی اسلات |
| `/patients/` | patients | پرونده مراجعان |
| `/records/` | records | جلسات، یادداشت‌ها |
| `/clinic/` | clinic | اتاق‌ها، تنظیمات، حضور |
| `/documents/` | documents | مدارک |
| `/finance/` | finance | مالی |
| `/core/` | core | جست‌وجوی سراسری |
| `/backup/` | backup | پشتیبان |
| `/audit/` | audit | گزارش فعالیت‌ها |
| `/reports/` | reports | گزارش‌های مدیریتی |
| `/licensing/` | licensing | لایسنس |
| `/notifications/` | notifications | اعلان‌ها |
| `/` | dashboard | داشبورد اصلی |
| `/media/` | (فقط `DEBUG=True`) | فایل‌های آپلودی |

**⚠️ نکته‌ی مهم:** اپ `appointments` **URL مستقل ندارد**. مدل `Appointment` از طریق `Session.appointment` (OneToOne) و ویوهای `records` مدیریت می‌شود.

### URLهای کلیدی `accounts/urls.py`

| نام | مسیر | کاربرد |
|-----|------|--------|
| `login` | `/accounts/login/` | ورود |
| `logout` | `/accounts/logout/` | خروج |
| `secretary_dashboard` | `/accounts/secretary/dashboard/` | داشبورد منشی |
| `user_list`, `user_create`, `user_edit`, `user_toggle_active`, `user_change_password` | `/accounts/users/...` | مدیریت کاربران |
| `consultant_level_list/create/edit/toggle/delete` | `/accounts/levels/...` | سطوح مشاور |
| `consultants_schedule_list` | `/accounts/consultants/` | لیست برنامه‌ها |
| `consultant_weekly_schedule` | `/accounts/consultants/<pk>/schedule/` | برنامه هفتگی |
| `consultant_month_schedule` | `/accounts/consultants/<pk>/month/` | تقویم ماهانه |
| `api_save_day_schedule`, `api_reset_day_schedule` | `/accounts/consultants/<pk>/day/...` | API |
| `consultant_exceptions`, `consultant_exception_create`, `consultant_exception_delete` | `/accounts/consultants/<pk>/exceptions/...` | مرخصی و استثنا |
| `slot_search` | `/accounts/slots/search/` | جست‌وجوی نوبت |
| `api_day_slots` | `/accounts/slots/<pk>/day/` | اسلات‌های روز |

### URLهای دیگر (از `base.html` استخراج شده)

`global_search`, `patient_list`, `patient_create`, `session_list`, `session_create`,
`finance_dashboard`, `transaction_list`, `transaction_create`, `room_list`,
`reports_dashboard`, `clinic_settings`, `backup_list`, `audit_list`, `license_dashboard`,
`notifications_list`, `dashboard`

---

## ۴. الگوهای معماری

### 🔐 ۱) احراز هویت با کد ملی

```python
AUTH_USER_MODEL = "accounts.User"
USERNAME_FIELD = "national_code"
username = None
UserManager.create_user() و create_superuser() سفارشی. سوپریوزر خودکار نقش manager می‌گیرد.

نقش‌ها:

manager — مدیر مرکز (همه دسترسی)

consultant — مشاور

secretary — منشی

🛡️ ۲) RBAC دو لایه
سیستم دسترسی در دو لایه موازی کار می‌کند:

لایه ۱: accounts/permissions.py — توابع is_* و can_*

لایه ۲: accounts/decorators.py — دکوراتورها:

@manager_required, @consultant_required, @secretary_required

@medical_view_required, @medical_edit_required

@narrative_view_required, @narrative_edit_required

@finance_view_required, @finance_edit_required

@appointments_required, @timer_control_required

@presence_manage_required

@client_register_required

@session_view_required, @session_note_required

لایه ۳: accounts/templatetags/role_tags.py — فیلترهای قالب:

django
{% if user|is_manager %}...{% endif %}
{% if user|can_view_session_note %}...{% endif %}
قواعد دسترسی کلیدی:

نقش	بالینی	شرح حال	مالی	تایمر	یادداشت جلسه
manager	✅	✅	✅	✅	✅
consultant	✅	فقط مراجعین خودش	فقط مشاهده	❌	فقط جلسات خودش
secretary	❌	❌	✅ ویرایش	✅	❌
نکته‌ی مهم can_view_narrative: مشاور فقط اگر assigned_consultant باشد یا قبلاً جلسه‌ای با مراجع داشته باشد.

Aliasهای legacy: is_physician و physician_required هنوز به‌عنوان alias برای is_consultant و consultant_required وجود دارند.

💰 ۳) سطح مشاور (ConsultantLevel) — هسته‌ی مالی
فیلد	توضیح
name, code, order	شناسه
standard_minutes	زمان استاندارد (پیش‌فرض ۴۵)
base_price	مبلغ پایه جلسه
overtime_per_minute	هزینه هر دقیقه مازاد
grace_minutes	دقایق ارفاق (پیش‌فرض ۵)
rounding_minutes	رُند (۰=بدون، ۵=هر ۵ دقیقه)
max_minutes	حداکثر زمان (۱۲۰)
insurance_share	سهم بیمه
effective_from, effective_to	بازه اعتبار
color, is_active	نمایش
متد snapshot(): اسنپ‌شات JSON برای ذخیره در Session.level_snapshot — تضمین می‌کند تغییر تعرفه بعداً روی جلسات قدیمی اثر نگذارد.

الگوریتم محاسبه هزینه (records.calculate_session_fee):

python
if duration <= standard + grace:
    return base_price
overage = duration - standard - grace
if rounding > 0:
    overage = ceil(overage / rounding) * rounding
return base_price + overage * overtime_rate
📅 ۴) تاریخ شمسی
accounts/templatetags/jalali_tags.py:

فیلتر	خروجی
jalali	۱۴۰۵/۰۷/۰۳
jalali_datetime	۱۴۰۵/۰۷/۰۳ — ۱۴:۳۰
jalali_full	۳ مهر ۱۴۰۵
jalali_short	۳ مهر
jalali_time	۱۴:۳۰
jalali_weekday	شنبه
fa_num	ارقام فارسی
الگوی تبدیل timezone-safe:

python
if hasattr(value, "tzinfo") and value.tzinfo is not None:
    value = timezone.localtime(value).replace(tzinfo=None)
j = jdatetime.datetime.fromgregorian(datetime=value)
🔢 ۵) اعداد فارسی
accounts/templatetags/persian_numbers.py:

فیلتر	خروجی
pnum	۱٬۲۰۰٬۰۰۰ (جداکننده فارسی + ارقام فارسی)
ptoman	۸۰۰٬۰۰۰ تومان (مقدار صفر → —)
جداکننده: ٬ (U+066C — Arabic thousands separator)

🔑 ۶) Licensing + Trial — سه‌لایه ضدتقلب
مدل‌ها: License + TrialState

Trial ۱۴ روزه با ۳ لایه ذخیره‌سازی (licensing/services.py):

لایه	مسیر
DB	TrialState
File	~/.tabib/install.json (⚠️ هنوز tabib!) — HMAC-SHA256 signed
Registry	HKCU\Software\Tabib\Install (⚠️ هنوز tabib!)
الگوریتم ضدتقلب:

امضا = HMAC-SHA256(SECRET_KEY + fingerprint, payload)

از ۳ منبع می‌خواند، قدیمی‌ترین تاریخ را انتخاب می‌کند

fingerprint = MAC آدرس (از licensing/fingerprint.py)

API عمومی:

python
from licensing.services import is_app_usable, get_trial_info
usable, mode = is_app_usable()  # mode: "license" | "trial" | "expired"
info = get_trial_info()  # {first_run, elapsed_days, remaining_days, ...}
Middleware: LicenseMiddleware — تمام مسیرها را قفل می‌کند مگر مسیرهای exempt:

python
EXEMPT_PREFIXES = [
    "/accounts/login/", "/accounts/logout/", "/licensing/",
    "/admin/", "/static/", "/media/",
]
سوپریوزر همیشه آزاد + fail-safe روی خطا (اجازه‌ی عبور می‌دهد تا سامانه کامل قفل نشود).

دکوراتور:

python
@feature_required("finance")   # ← اول
@manager_required
def view(...): ...
Context Processor: license_status → {% current_license %} در قالب.

تگ‌های قالب license_tags: current_license, has_feature

📋 ۷) Audit Log
audit/models.py:

python
from audit.models import log_action
log_action(request, "create", obj, description="...")
فیلدها: user, user_display (اسنپ‌شات), action (۱۱ نوع), model_name, object_id, object_repr, description, ip_address, user_agent, created_at.

۱۱ نوع action: create, update, delete, view, login, logout, login_failed, export, print, backup, restore, other.

Fail-safe: خطا در ثبت Audit سامانه را متوقف نمی‌کند.

🎨 ۸) رابط کاربری
قالب اصلی: templates/base.html

ویژگی‌ها:

راست‌چین، فونت Vazirmatn، Bootstrap RTL

سایدبار تیره + موبایل همبرگر

Toast Notification (به‌جای Alert)

Confirm Modal سفارشی

Payment Modal (با quick amounts ۱۰۰٪/۵۰٪/۲۵٪ و ۳ روش پرداخت)

اعلان‌ها به‌صورت dropdown (با AJAX)

Ctrl+K → فوکوس روی جست‌وجو

پالت رنگی:

css
--primary: #2563eb;    /* آبی */
--secondary: #06b6d4;  /* فیروزه‌ای */
--success: #10b981;    /* سبز */
--danger: #ef4444;     /* قرمز */
--warning: #f59e0b;    /* نارنجی */
فایل‌های static:

css/base.css, css/modals.css

js/base.js, js/modals.js, js/jalali-datepicker.js

CDNها:

Bootstrap 5.3.3 RTL

Vazirmatn 33.003

Bootstrap Icons 1.11.3

persian-datepicker 1.2.0

jQuery 3.7.1 (فقط برای persian-datepicker)

persian-date 1.1.0

۵. مدل‌های کامل دیتابیس
👤 accounts.User
python
class User(AbstractUser):
    username = None
    first_name  # "نام" — اجباری
    last_name   # "نام خانوادگی" — اجباری
    national_code  # unique, USERNAME_FIELD
    role  # consultant/secretary/manager
    phone
    consultant_level  # FK → ConsultantLevel (PROTECT)
    bio  # رزومه
    specialties  # JSONField لیست
Propertyها: is_consultant, is_secretary, is_manager

💰 accounts.ConsultantLevel
جزئیات در بخش ۴-۳.

📅 accounts.ConsultantWeeklySchedule
consultant, weekday (0=شنبه ... 6=جمعه)

start_time, end_time

blocked_hours (JSONField — مثلاً [12, 13])

unique_together = [("consultant", "weekday")]

🚫 accounts.ConsultantScheduleOverride
consultant, from_date, to_date

is_off (تعطیلی کامل)

custom_start, custom_end (ساعت ویژه)

blocked_hours

apply_to_all_weekdays (پیش‌فرض True)

reason, created_by, created_at

⚙️ accounts.ConsultantSlotSettings
consultant (OneToOne)

slot_minutes (پیش‌فرض ۵۰)

buffer_minutes

max_daily_sessions (پیش‌فرض ۸)

allow_overlap (گروه‌درمانی)

📜 accounts.ScheduleChangeLog
consultant, changed_by, date

change_type (۶ نوع: activate/deactivate/time_change/leave/room_change/bulk_update)

before, after (JSONField)

reason, created_at

🕐 accounts.SecretaryShift
secretary, date, start_time, end_time

section: reception / followup / finance / full

is_active

📅 appointments
WeeklySchedule (legacy — نباید استفاده شود):

physician (بازمانده)، day_of_week, start_time, end_time, slot_duration, is_active

related_name="legacy_weekly_schedules"

TimeOff:

physician, date, all_day, start_time, end_time

reason: vacation/holiday/sick/conference/personal/other

note

Appointment:

گروه	فیلد
مرجع	patient, physician, date, start_time, end_time
وضعیت	status: scheduled/confirmed/arrived/in_progress/completed/cancelled/no_show
منبع	source: in_person/phone/online
علت	reason, note
تبدیل	visit (OneToOne → records.Visit)
پرداخت	payment_status, payment_amount, payment_method, transaction_id, paid_at
پیامک	confirmation_sent, confirmation_sent_at, reminder_sent, reminder_sent_at, reminder_response
متادیتا	created_by, created_at, updated_at
متد clean(): چک تداخل زمانی با نوبت‌های فعال مشاور.

Propertyها: status_badge, payment_badge, is_paid, duration_minutes, is_today

👥 patients.Patient
اطلاعات هویتی: file_number (خودکار 5 رقمی)، first_name, last_name, father_name, national_code (اعتبارسنجی ایران)، is_foreign, foreign_id, gender, birth_date, marital_status, job, education

تماس: phone, mobile (اعتبارسنجی ایران)، emergency_phone, emergency_name

آدرس: country, province, city, district, street, alley, plaque, postal_code, address_note

ویژه مشاوره:

referral_source (۹ منبع: self/friend/doctor/internet/instagram/school/court/insurance/other)

guardian_name, guardian_phone (برای زیر ۱۸ سال)

confidentiality_level: normal/confidential/special

assigned_consultant (FK → User)

مالی: outstanding_balance, credit_limit (۰ = بدون سقف)

Propertyها: full_name, age, is_minor

متد save(): دو بار save (بار اول pk، بار دوم file_number).

🩺 patients.ClientNarrative (شرح حال محرمانه)
client (OneToOne → Patient)

chief_complaint, history_of_present_illness

past_psychiatric_history, family_history, medical_history, medications, substance_use

social_history, education_occupation, marital_family_status

suicide_risk, self_harm_risk (none/low/moderate/high)

risk_notes

provisional_diagnosis, dsm_codes (JSONField)

created_by, created_at, updated_at, last_updated_by

Property: has_risk

📋 records.Visit (legacy)
patient, physician, visited_at, prescription_serial (خودکار V-YYYY-00001)

chief_complaint, history, brief_history, diagnosis, treatment_plan, follow_up

🎯 records.Session (هسته‌ی جلسه مشاوره)
اتصالات: client (Patient), consultant (User), room (Room), appointment (OneToOne → Appointment)

اسنپ‌شات: level_snapshot (JSONField — مهم برای تاریخی بودن)

زمان‌بندی: scheduled_start, scheduled_end, started_at, ended_at, actual_duration_minutes

Pause: pause_started_at, total_paused_seconds

نوع: session_type (individual/couple/family/group/phone/online), session_number, extension_reason, secretary_note

مالی: calculated_fee, discount_percent, final_fee, payment_status (pending/paid/deferred/partial/insurance/waived), payment_method (cash/card/online/insurance/wallet/other), paid_at, paid_amount, remaining_amount, payment_note

وضعیت: status (scheduled/in_progress/paused/awaiting_payment/completed/cancelled/no_show)

متدها:

start() — شروع (scheduled/paused → in_progress)

pause() — وقفه

resume() — ادامه با محاسبه elapsed pause

end() — پایان + محاسبه خودکار fee

effective_duration_minutes() — مدت مؤثر (کل - وقفه‌ها)

elapsed_seconds() — ثانیه سپری‌شده (زنده)

remaining_seconds() — باقی‌مانده تا استاندارد

is_overtime() — از grace گذشته؟

current_fee() — هزینه لحظه‌ای (نمایش زنده)

register_payment(amount, method, note) — ثبت پرداخت

defer_payment(note) — نسیه

تابع کمکی: records.calculate_session_fee(duration, snapshot) — الگوریتم در بخش ۴-۳.

📝 records.SessionNote
محتوا: content (متن تحلیل)

صوتی: has_audio, audio_file, audio_duration_seconds, audio_size_bytes, audio_format

متن تبدیل: transcript, transcript_source (whisper/manual/voice_typing/vosk), transcript_edited, transcript_edited_at

SOAP: soap_subjective, soap_objective, soap_assessment, soap_plan

تگ‌ها: tags (JSONField), severity (mild/moderate/severe), progress (better/no_change/worse)

AI (آینده): ai_summary, ai_key_topics, ai_sentiment

متادیتا: created_by, created_at, updated_at, version, status (draft/finalized/signed), finalized_at

Propertyها: full_text, effective_duration_minutes

📚 records.SessionNoteRevision
note (FK → SessionNote), version

content, transcript

changed_by, changed_at, change_reason

unique_together = [("note", "version")]

هدف: نسخه‌بندی — برای تحلیل الگوی فکری مشاور.

💰 finance.Transaction
دسته‌ها:

درآمد: visit_fee, service, product_sale, other_income

هزینه: purchase, rent, salary, equipment, current_expense, other_expense

فیلدها: receipt_number (خودکار RC-YYYY-XXXXX درآمد / PY-YYYY-XXXXX هزینه)، transaction_type, category, amount, transaction_date, description, patient (nullable)، visit (nullable), created_by, created_at

🏢 clinic
ClinicSettings (Singleton — pk=1):

اطلاعات پایه: clinic_name, manager_name, specialty, license_number, phone, mobile, address, logo

متون چاپی: footer_note, invoice_header

نوبت‌دهی: require_payment_for_appointment, default_appointment_fee, appointment_slot_duration

بازه رزرو: booking_horizon_months (پیش‌فرض ۶)

متد: ClinicSettings.get() — get_or_create(pk=1)

Room:

name, code (خودکار room-{pk}), capacity, color, equipment, order, is_active

ConsultantDailyPresence:

consultant, date, room, arrived_at, left_at

status: present/in_session/on_break/left

unique_together = [("consultant", "date")]

Property: is_present

ConsultantRoomChange:

consultant, date, from_room, to_room, changed_at, changed_by, note

🔔 notifications.Notification
recipient (FK → User)

type — ۷ نوع: schedule_changed/leave_request/new_session/session_overdue/payment_deferred/survey_response/system_alert

title, message, link

payload (JSONField)

is_read, read_at

created_at (indexed)

متد mark_read()

ایندکس: (recipient, is_read, -created_at)

🔑 licensing.License
شناسه: license_key (خودکار — TABIB-XXXX-... ⚠️)، serial_number (خودکار SN-YYYY-XXXXXXXX)

نوع: tier: trial/basic/pro/enterprise

مالک: licensed_to, licensed_email, licensed_phone

محدودیت: max_users, max_physicians (⚠️ legacy)، max_branches

Feature flags: enable_inventory⚠️, enable_finance, enable_therapies⚠️, enable_documents, enable_consent⚠️, enable_reports, enable_backup, enable_audit, enable_appointments

تاریخ: activated_at, valid_from, valid_until, last_check

وضعیت: status: active/expired/suspended/not_activated، is_active

نصب: installation_id (MD5 از uuid.getnode())

متدها:

is_valid, days_remaining, is_expiring_soon, status_display_badge

activate(days=365), deactivate(), check_and_update_status()

License.get_current() — لایسنس فعال

License.feature_enabled(name)

🔑 licensing.TrialState
first_run_date, machine_fingerprint, created_at

📋 audit.AuditLog
فیلدها در بخش ۴-۷.

💾 backup.BackupRecord
file_name, file_size, created_at, created_by, status (success/failed), note

Property: size_display (بایت/کیلوبایت/مگابایت)

۶. فایل‌های حساس / مهم
فایل	چرا مهم است
config/settings.py	تمام تنظیمات
config/urls.py	نقشه URLها
templates/base.html	قالب اصلی
accounts/models.py	هسته مدل‌ها
accounts/permissions.py	هسته RBAC (توابع)
accounts/decorators.py	دکوراتورهای RBAC
accounts/templatetags/role_tags.py	فیلترهای RBAC
accounts/templatetags/jalali_tags.py	تاریخ شمسی
accounts/templatetags/persian_numbers.py	اعداد فارسی
accounts/views/consultants/__init__.py	re-export ویوها
appointments/models.py	Appointment + TimeOff
patients/models.py	Patient + Narrative
records/models.py	Session + محاسبه هزینه
clinic/models.py	Room + تنظیمات
licensing/services.py	Trial ۳ لایه
licensing/middleware.py	قفل سامانه
licensing/decorators.py	feature_required
audit/models.py::log_action	ثبت فعالیت
۷. راهنمای نصب و اجرا
پیش‌نیازها
Python 3.11+

pip

Git

نصب
bash
cd D:\projects\moshaver
python -m venv venv
venv\Scripts\activate          # ویندوز
source venv/bin/activate       # لینوکس/مک

pip install -r requirements.txt
copy .env.example .env
# ویرایش .env — حداقل SECRET_KEY

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
# کد ملی، نام، نام خانوادگی، رمز
# نقش خودکار: manager

python manage.py runserver
آدرس‌های کلیدی
آدرس	کاربرد
/	داشبورد
/admin/	پنل ادمین
/accounts/login/	ورود
/patients/	مراجعان
/records/	جلسات
/clinic/	تنظیمات و اتاق‌ها
/finance/	مالی
/reports/	گزارش‌ها
/licensing/	لایسنس
/notifications/	اعلان‌ها
۸. راهنمای استقرار (Production)
.env نمونه
env
SECRET_KEY=<کلید-تصادفی-بلند-حداقل-۵۰-کاراکتر>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

USE_POSTGRES=True
DB_NAME=moshaver
DB_USER=moshaver_user
DB_PASSWORD=<رمز-قوی>
DB_HOST=localhost
DB_PORT=5432

CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECURE_SSL_REDIRECT=True
گام‌ها
bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py check --deploy
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
۹. تله‌ها و بدهی‌های فنی
⚠️ ۱) لایسنس هنوز برند «طبیب» دارد
مورد	مقدار فعلی	باید بشه
پیشوند کلید	TABIB-	MSHV- یا مشابه
پوشه مخفی	~/.tabib/install.json	~/.moshaver/...
رجیستری	HKCU\Software\Tabib\Install	Software\Moshaver\Install
فیلد محدودیت	max_physicians	max_consultants
Feature flag	enable_inventory	❌ حذف
Feature flag	enable_therapies	❌ حذف
Feature flag	enable_consent	❌ حذف
Feature flag	—	enable_notifications (اضافه شود)
⚠️ ۲) دوگانگی physician / consultant
اپ appointments هنوز از physician استفاده می‌کند. در appointments/models.py، TimeOff.physician، Appointment.physician، WeeklySchedule.physician.

Aliasهای سازگاری در accounts/permissions.py و accounts/decorators.py:

python
is_physician = is_consultant
physician_required = consultant_required
پیشنهاد آینده: مایگریشن rename.

⚠️ ۳) WeeklySchedule legacy
مدل قدیمی در appointments با related_name="legacy_weekly_schedules". نباید استفاده شود. جایگزینش ConsultantWeeklySchedule در accounts است.

⚠️ ۴) appointments URL مستقل ندارد
config/urls.py خط appointments/ ندارد. Session از Appointment به‌صورت OneToOne استفاده می‌کند و از طریق ویوهای records مدیریت می‌شود.

⚠️ ۵) documents مدل‌ها دیده نشده
فایل documents/models.py در این سند بررسی نشده.

⚠️ ۶) Django 5.2 vs Python 3.14
forms.CharField("label", ...) → forms.CharField(label="label", ...)

⚠️ ۷) jdatetime و timezone
python
local_naive = timezone.localtime(value).replace(tzinfo=None)
j = jdatetime.datetime.fromgregorian(datetime=local_naive)
⚠️ ۸) Circular Imports
import داخل تابع، نه بالای فایل. مثال در permissions.py::can_view_narrative که Session را داخل تابع import می‌کند.

⚠️ ۹) Static Files
در DEBUG=False باید whitenoise فعال و collectstatic اجرا شود.

⚠️ ۱۰) ترتیب دکوراتورها
python
@feature_required("finance")   # ✅ اول
@manager_required
def ...: ...
⚠️ ۱۱) SQLite WAL
در settings.py تنظیم شده (journal_mode=WAL, mmap_size=128MB, ...). در production حتماً PostgreSQL.

⚠️ ۱۲) Patient.save() دو بار save
بار اول برای pk، بار دوم برای file_number.

⚠️ ۱۳) LicenseMiddleware fail-safe
در صورت خطا در is_app_usable()، اجازه‌ی عبور می‌دهد تا سامانه کامل قفل نشود. ریسک امنیتی جزئی — اگر services خراب شود، سامانه بدون لایسنس کار می‌کند.

۱۰. الگوهای کدنویسی
View استاندارد
python
@feature_required("module_name")
@permission_decorator
def view_name(request, ...):
    # ۱. خواندن داده
    # ۲. پردازش (POST)
    # ۳. ثبت Audit
    # ۴. پیام موفقیت
    # ۵. redirect یا render
Form استاندارد
python
class MyForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = (...)
        widgets = {...}

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop("patient", None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
Template استاندارد
django
{% extends "base.html" %}
{% load jalali_tags persian_numbers role_tags %}
{% block title %}عنوان{% endblock %}
{% block header %}<i class="bi bi-icon"></i> عنوان{% endblock %}
{% block content %}
    <div class="card">...</div>
{% endblock %}
ریفکتور به پکیج
الگوی consultants: فایل بزرگ → پوشه با زیرماژول‌ها → re-export در __init__.py → urls.py دست‌نخورده.

Audit
python
from audit.models import log_action
log_action(request, "create", obj, description="...")
Notification
python
from notifications.models import Notification
Notification.objects.create(
    recipient=user,
    type="schedule_changed",
    title="...",
    message="...",
    link="/accounts/...",
    payload={...},
)
۱۱. Roadmap
✅ تکمیل‌شده
فاز ۱: پایه (احراز هویت، RBAC، لایسنس، Audit)

فاز ۲: services برنامه‌ریزی مشاور + get_availability + generate_slots

فاز ۳: سطح مشاور + تقویم شمسی + اعداد فارسی

فاز ۴: جلسات + شروع/پایان/Pause + پرداخت + نسیه

فاز ۵: صفحه مراجع + جلسات + API + تقویم شمسی

ماژول اعلان‌ها

ریفکتور consultants به پکیج

Trial ۳ لایه ضدتقلب

🟡 در حال انجام
اصلاحات فاز ۵

بازنویسی WeeklySchedule legacy

تغییر نام physician → consultant

رفع برند tabib از لایسنس

🔴 باقی‌مانده
□ خروجی PDF گزارش‌ها
□ SMS واقعی
□ درگاه پرداخت
□ پرسش‌نامه‌های استاندارد روانشناسی (PHQ-9، GAD-7)
□ نوبت‌دهی آنلاین برای مراجع
□ اپلیکیشن موبایل (Flutter)
□ AI برای تحلیل یادداشت‌ها (مدل آماده است)
□ تست‌های واحد و یکپارچه
۱۲. اطلاعات پروژه
پروژه: مشاور — سامانه جامع مدیریت مرکز مشاوره
منشأ: منشعب از «طبیب»
توسعه: با کمک AI

📌 پایان
هر توسعه‌دهنده یا AI جدید باید:

این سند را کامل بخواند

AI_CONTEXT.md را بخواند

config/settings.py, config/urls.py, accounts/models.py را ببیند

templates/base.html را ببیند

records/models.py و appointments/models.py را ببیند

text

---

# 📄 فایل نهایی ۲: `AI_CONTEXT.md`

```markdown
# 🤖 AI Context — پروژه «مشاور»

> اگر یک AI (ChatGPT, Claude, Cursor, Copilot) روی این پروژه کار می‌کند، این فایل را قبل از هر تغییری بخواند.

---

## ۱. Context

**پروژه:** سامانه‌ی مدیریت مرکز مشاوره (فارسی، راست‌چین)
**هدف:** نوبت‌دهی، پرونده مراجعان، جلسات مشاوره با تایمر زنده، شرح حال محرمانه، مالی، گزارش، اعلان، لایسنس، مدیریت مشاوران و منشی‌ها
**منشأ:** منشعب از «طبیب» — برخی اپ‌ها حذف، برخی تغییر، برخی اضافه

**مخاطبین:**
- `manager` — مدیر مرکز (همه دسترسی)
- `consultant` — مشاور (برگزارکننده جلسه)
- `secretary` — منشی (پذیرش، مالی، تایمر — بدون شرح حال)

**زبان UI:** فارسی | **زبان کد:** انگلیسی

---

## ۲. Glossary

| اصطلاح | معنی |
|--------|------|
| **مشاور** (consultant) | کاربری که جلسه برگزار می‌کند |
| **مراجع** (patient / client) | مراجعه‌کننده — کاربر سیستم نیست |
| **جلسه** (session) | واحد مشاوره — دارای تایمر و Pause |
| **سطح مشاور** (ConsultantLevel) | تعیین‌کننده تعرفه |
| **اسنپ‌شات** (snapshot) | JSON ذخیره‌شده روی `Session.level_snapshot` — تاریخی |
| **اسلات** (slot) | بازه زمانی قابل رزرو |
| **ارفاق** (grace) | دقایق اول بعد از استاندارد که رایگان |
| **رُند** (rounding) | گرد کردن زمان مازاد |
| **Override** | استثنا روی برنامه هفتگی |
| **Trial** | دوره آزمایشی ۱۴ روزه با ۳ لایه ضدتقلب |
| **Feature Flag** | `enable_finance`, `enable_notifications`, ... |
| **legacy** | کد بازمانده از «طبیب» |

---

## ۳. Tech Stack

- **Django:** 5.2+ (< 7.0) | **Python:** 3.11+
- **DB:** SQLite (dev) / PostgreSQL (prod) — `USE_POSTGRES`
- **Frontend:** Bootstrap RTL + Vazirmatn + persian-datepicker
- **Auth:** کد ملی (`national_code`) به‌جای username
- **API:** ❌ DRF استفاده نشده — `JsonResponse` خالص
- **Server:** Gunicorn + WhiteNoise
- **Env:** python-decouple | **تاریخ شمسی:** jdatetime
- **API calls از frontend:** فقط برای notifications dropdown + schedule API

---

## ۴. Directory Map
config/ → settings, urls, wsgi, asgi
accounts/ → User, RBAC, ConsultantLevel, برنامه, شیفت
├── views/consultants/ → پکیج (levels, schedule, exceptions, api, search)
├── templatetags/ → jalali_tags, persian_numbers, role_tags
├── permissions.py → توابع دسترسی
└── decorators.py → دکوراتورهای RBAC
appointments/ → Appointment, TimeOff, WeeklySchedule (legacy)
patients/ → Patient, ClientNarrative
records/ → Visit (legacy), Session, SessionNote, SessionNoteRevision
finance/ → Transaction
clinic/ → ClinicSettings, Room, Presence, RoomChange
notifications/ → Notification
licensing/ → License, TrialState, middleware, services, fingerprint
audit/ → AuditLog, log_action()
backup/ → BackupRecord
documents/ → (مدل‌ها دیده نشده)
reports/ → بدون مدل
core/ → بدون مدل (جست‌وجو)
templates/base.html → ★ قالب اصلی

text

---

## ۵. Core Concepts

### 5.1 User & Roles
```python
class Role(models.TextChoices):
    CONSULTANT = "consultant", "مشاور"
    SECRETARY  = "secretary",  "منشی"
    MANAGER    = "manager",    "مدیر مرکز"
USERNAME_FIELD = "national_code", username = None

first_name, last_name اجباری

consultant_level فقط برای مشاور

specialties → JSONField لیست

Propertyها: is_consultant, is_secretary, is_manager

5.2 ConsultantLevel
تعرفه: standard_minutes (۴۵), base_price, overtime_per_minute,
grace_minutes (۵), rounding_minutes (۵), max_minutes (۱۲۰), insurance_share.
متد snapshot() → JSON.

5.3 برنامه‌ی مشاور (در accounts)
ConsultantWeeklySchedule — الگوی تکرارشونده (weekday: 0=شنبه، 6=جمعه)

ConsultantScheduleOverride — استثنا در بازه تاریخ

ConsultantSlotSettings — slot_minutes (۵۰), buffer_minutes, max_daily_sessions (۸)

ScheduleChangeLog — تاریخچه با before/after JSON

5.4 Appointment (در appointments)
هنوز از physician استفاده می‌کند (legacy)

وضعیت: scheduled/confirmed/arrived/in_progress/completed/cancelled/no_show

پرداخت: not_required/unpaid/pending/paid/refunded/failed

visit OneToOne با records.Visit (legacy)

متد clean() — چک تداخل زمانی

Propertyها: status_badge, payment_badge, is_paid, duration_minutes, is_today

5.5 Session (در records) — هسته
client, consultant, room, appointment (OneToOne)

level_snapshot (JSONField — تاریخی)

scheduled_start/end, started_at, ended_at, actual_duration_minutes

pause_started_at, total_paused_seconds

session_type (individual/couple/family/group/phone/online)

مالی: calculated_fee, discount_percent, final_fee, paid_amount, remaining_amount

status: scheduled/in_progress/paused/awaiting_payment/completed/cancelled/no_show

متدهای حیاتی:

python
session.start()         # scheduled/paused → in_progress
session.pause()         # in_progress → paused
session.resume()        # paused → in_progress (با محاسبه pause)
session.end()           # پایان + محاسبه خودکار fee
session.elapsed_seconds()   # زنده — از started_at تا الان منهای pauseها
session.remaining_seconds() # باقی‌مانده تا standard
session.current_fee()       # هزینه لحظه‌ای (نمایش زنده)
session.register_payment(amount, method, note)
session.defer_payment(note) # نسیه
5.6 محاسبه هزینه
python
def calculate_session_fee(duration, level_snapshot):
    if duration <= standard + grace:
        return base_price
    overage = duration - standard - grace
    if rounding > 0:
        overage = ceil(overage / rounding) * rounding
    return base_price + overage * overtime_rate
5.7 SessionNote (یادداشت)
content, transcript (Whisper/manual/voice_typing/vosk)

SOAP: soap_subjective/objective/assessment/plan

severity, progress, tags (JSON)

AI fields آماده: ai_summary, ai_key_topics, ai_sentiment

status: draft/finalized/signed

SessionNoteRevision — نسخه‌بندی

5.8 TimeOff (در appointments)
physician, date, all_day, start_time, end_time,
reason (vacation/holiday/sick/conference/personal/other)

5.9 WeeklySchedule (legacy)
مدل قدیمی در appointments با related_name="legacy_weekly_schedules".
نباید استفاده شود. جایگزینش ConsultantWeeklySchedule است.

5.10 SecretaryShift
section: reception, followup, finance, full

5.11 پکیج consultants
__init__.py همه توابع را re-export می‌کند — urls.py بدون تغییر:

python
from .levels import consultant_level_list, ...
from .schedule import consultants_schedule_list, ...
from .exceptions import consultant_exceptions, ...
from .api import api_save_day_schedule, api_reset_day_schedule
from .search import slot_search, api_day_slots
5.12 Patient
file_number خودکار (5 رقمی)

national_code با اعتبارسنجی ایران (nullable برای اتباع)

mobile اعتبارسنجی ایران

assigned_consultant (FK → User)

confidentiality_level: normal/confidential/special

outstanding_balance, credit_limit (۰ = بدون سقف)

Property: age, is_minor, full_name

5.13 ClientNarrative (شرح حال)
OneToOne با Patient

suicide_risk, self_harm_risk (none/low/moderate/high)

dsm_codes (JSONField)

Property: has_risk

5.14 ClinicSettings (Singleton)
pk=1 همیشه

require_payment_for_appointment, default_appointment_fee, appointment_slot_duration

ClinicSettings.get()

5.15 Room + Presence
Room — code خودکار room-{pk}

ConsultantDailyPresence — unique_together = [("consultant", "date")]

5.16 Notification
recipient, type (۷ نوع), title, message, link, payload

is_read, read_at

متد mark_read()

5.17 Licensing
License.get_current() → لایسنس فعال

License.feature_enabled(name) → boolean

is_app_usable() → (bool, mode) — mode: license/trial/expired

get_trial_info() → {first_run, elapsed_days, remaining_days, ...}

Trial ۳ لایه:

DB (TrialState)

File ~/.tabib/install.json (⚠️ legacy branding) — HMAC-SHA256

Registry HKCU\Software\Tabib\Install (⚠️ legacy branding)

الگوریتم: از ۳ منبع می‌خواند، قدیمی‌ترین تاریخ را انتخاب.

Middleware (LicenseMiddleware): مسیرهای exempt:

python
["/accounts/login/", "/accounts/logout/", "/licensing/", "/admin/", "/static/", "/media/"]
سوپریوزر همیشه آزاد. Fail-safe روی خطا (اجازه عبور).

Decorator:

python
@feature_required("finance")   # ← اول
@manager_required
5.18 Audit
python
from audit.models import log_action
log_action(request, "create", obj, description="...")
۱۱ نوع action: create/update/delete/view/login/logout/login_failed/export/print/backup/restore/other

5.19 تاریخ شمسی
فیلترها: jalali, jalali_datetime, jalali_full, jalali_short, jalali_time, jalali_weekday, fa_num

اعداد فارسی: pnum, ptoman

همیشه timezone.localtime() قبل از jdatetime

5.20 URL Map
config/urls.py:

text
/admin/         → Django admin
/accounts/      → accounts.urls (ورود، مشاوران، سطوح، برنامه، اسلات‌ها)
/patients/      → patients.urls
/records/       → records.urls (جلسات، یادداشت‌ها)
/clinic/        → clinic.urls (اتاق، حضور، تنظیمات)
/documents/     → documents.urls
/finance/       → finance.urls
/core/          → core.urls (جست‌وجو)
/backup/        → backup.urls
/audit/         → audit.urls
/reports/       → reports.urls
/licensing/     → licensing.urls
/notifications/ → notifications.urls
/               → accounts.views.dashboard
/media/         → فقط در DEBUG
⚠️ appointments/ ندارد — Session از Appointment استفاده می‌کند.

۶. Coding Conventions
Views
Function-Based (نه Class-Based)

ترتیب: @feature_required(...) → @permission_decorator

import داخل تابع برای circular import

Forms
python
def __init__(self, *args, **kwargs):
    patient = kwargs.pop("patient", None)
    super().__init__(*args, **kwargs)
    for name, field in self.fields.items():
        field.widget.attrs.setdefault("class", "form-control")
Templates
{% extends "base.html" %}

{% load jalali_tags persian_numbers role_tags %}

بلاک‌ها: title, header, subtitle, topbar_actions, content, extra_css, extra_js

Toast به‌جای Alert

{{ obj.date|jalali }}, {{ price|ptoman }}

فیلترهای RBAC: {% if user|can_view_session %}, {% if user|is_manager %}

Naming
فایل/متغیر: انگلیسی snake_case

verbose_name و UI: فارسی

کامیت: فارسی با پیشوند (refactor:, feat:, fix:)

Audit
هر عملیات مهم:

python
from audit.models import log_action
log_action(request, "create", obj, description="...")
۷. Key Flows
7.1 نوبت‌دهی → جلسه
منشی → داشبورد

مشاور و تاریخ انتخاب

ConsultantWeeklySchedule + Override + SlotSettings → اسلات‌ها

Appointment ساخته می‌شود

Appointment.clean() — تداخل چک

اعلان برای مشاور

7.2 برگزاری جلسه (تایمر زنده)
Session.status = "scheduled"

منشی session.start() → started_at, in_progress

تایمر زنده در UI با session.elapsed_seconds()

مشاور می‌تواند session.pause() / session.resume()

session.end() → محاسبه actual_duration_minutes و calculated_fee

session.register_payment(amount, method) یا session.defer_payment()

7.3 ورود
کد ملی + رمز

LicenseMiddleware — is_app_usable()

اگر لایسنس معتبر یا trial فعال: عبور

اگر منقضی: licensing/expired.html (status 403)

7.4 ساخت Notification
python
Notification.objects.create(
    recipient=user,
    type="schedule_changed",
    title="برنامه‌ی شما تغییر کرد",
    message="...",
    link="/accounts/consultants/...",
    payload={"old": "...", "new": "..."},
)
7.5 ریفکتور به پکیج
الگوی consultants:

فایل views/foo.py → پوشه views/foo/

زیرماژول‌های منطقی

__init__.py re-export همه نام‌ها

urls.py دست‌نخورده

۸. What's Done / What's Not
✅ آماده
۱۳ اپ

احراز هویت با کد ملی

RBAC کامل ۲ لایه

ConsultantLevel + تعرفه + snapshot

برنامه هفتگی + استثنا + شیفت منشی + حضور + اتاق

Session با تایمر/Pause/Payment/نسیه

ClientNarrative (شرح حال)

SessionNote با SOAP و فیلدهای AI

تقویم شمسی + اعداد فارسی

لایسنس + Trial ۳ لایه

Notification (۷ نوع)

Audit + Backup

ClinicSettings Singleton

🟡 در حال انجام
اصلاحات پس از انشعاب

بازنویسی WeeklySchedule legacy

تغییر نام physician → consultant در appointments

رفع برند tabib از licensing (پوشه .tabib + رجیستری)

🔴 باقی‌مانده
PDF گزارش، SMS واقعی، درگاه پرداخت، پرسش‌نامه‌های روانشناسی، نوبت‌دهی آنلاین، اپ موبایل، AI برای یادداشت‌ها، تست‌ها

۹. Do's and Don'ts
✅ باید
قبل از تغییر، accounts/models.py, records/models.py, appointments/models.py را بخوان

برای عملیات مهم log_action بنویس

از ConsultantLevel.snapshot() استفاده کن

timezone.localtime() قبل از jdatetime

feature_required قبل از دکوراتور نقش

در پکیج‌ها همه نام‌ها را در __init__.py re-export کن

verbose_name فارسی، کد انگلیسی

برای Appointment از physician استفاده کن (فعلاً)، برای Session/ConsultantWeeklySchedule از consultant

برای کوئری‌های سنگین از select_related/prefetch_related استفاده کن

❌ نباید
username استفاده نکن — USERNAME_FIELD = "national_code"

request.user.username استفاده نکن

از WeeklySchedule legacy استفاده نکن

format قدیمی جنگو ("label", ...) را استفاده نکن

Circular import نساز — import داخل تابع

.env, db.sqlite3, media/, .venv/ را commit نکن

Alert جاوااسکریپت استفاده نکن

PROJECT_HANDBOOK.md را با محتوای «طبیب» جایگزین نکن

accounts/views/consultants.py را دوباره نساز — پکیج است

LicenseMiddleware را طوری تغییر نده که روی خطا، سامانه را قفل کند

Patient.save() را بدون توجه به file_number تغییر نده

۱۰. Quick Reference
دستورات
bash
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py check --deploy
Git (روی master)
bash
git add -A
git commit -m "feat: توضیح"
git push origin master
URLهای مهم
/, /admin/, /accounts/login/, /patients/, /records/, /clinic/,
/finance/, /reports/, /licensing/, /notifications/

فایل‌های کلیدی برای خواندن اول
config/settings.py

config/urls.py

accounts/models.py

accounts/permissions.py

records/models.py

appointments/models.py

accounts/views/consultants/__init__.py

licensing/services.py

templates/base.html

خطاهای رایج
خطا	راه‌حل
Unclosed tag	یک {% endif %} در base.html جا افتاده
Circular import	import داخل تابع
timezone + jdatetime	timezone.localtime().replace(tzinfo=None)
database is locked	SQLite WAL فعال است؛ برای prod PostgreSQL
FieldError: consultant	در Appointment از physician استفاده کن
AttributeError: consultants	accounts/views/consultants/ پکیج است، فایل نساز
TemplateDoesNotExist: license_tags	licensing/templatetags/license_tags.py باید باشد
TemplateSyntaxError: current_license	context processor licensing.context_processors.license_status فعال باشد
USERNAME_FIELD error	از national_code استفاده کن، نه username
۱۱. اطلاعات ریپو
GitHub: https://github.com/aliekos007-cloud/moshaver

برنچ اصلی: master

آخرین commit مهم: d89178d — افزودن اعلان‌ها + refactor مشاوران

📌 نکته‌ی نهایی برای AI
اگر شک داری چیزی از «طبیب» باقی مانده:

نشانه‌های legacy که باید بشناسی:
اپ‌های catalog, therapies, inventory, consent نباید باشند

نقش physician نباید به‌عنوان نقش باشد — فقط به‌عنوان نام فیلد در appointments (تا اصلاح)

WeeklySchedule در appointments — legacy

Visit در records — legacy

License.max_physicians, enable_inventory, enable_therapies, enable_consent — legacy

is_physician, physician_required — alias legacy

TABIB- prefix در license_key

~/.tabib/install.json و HKCU\Software\Tabib\Install — legacy trial paths

قبل از تغییر این چیزها، به کاربر بگو:
license_key — تغییر prefix نیاز به migration دارد

max_physicians — هر rename نیاز به migration دارد

WeeklySchedule legacy — حذف نیاز به migration دارد

Visit legacy — حذف نیاز به migration دارد

Trial file paths — کاربران فعلی trial خود را از دست می‌دهند

اگر AI جدید خواست شروع کند:
text
۱. PROJECT_HANDBOOK.md را بخوان
۲. AI_CONTEXT.md (این فایل) را بخوان
۳. config/settings.py + config/urls.py را ببین
۴. accounts/models.py + accounts/permissions.py را ببین
۵. records/models.py + appointments/models.py را ببین
۶. templates/base.html را ببین
سپس می‌تواند با اطمینان کار کند.

text

---

## 🎯 قدم نهایی

```bash
git rm PROJECT_HANDBOOK.md
git add PROJECT_HANDBOOK.md AI_CONTEXT.md
git commit -m "docs: اسناد نهایی PROJECT_HANDBOOK و AI_CONTEXT مطابق وضعیت واقعی"
git push origin master
📊 خلاصه‌ی چیزهایی که از پروژه‌ی تو فهمیدم
بخش	تعداد
اپ‌ها	۱۳
مدل‌ها	~۳۰
فیلترهای تاریخ شمسی	۷
فیلترهای RBAC	~۲۵
انواع اعلان	۷
انواع action در Audit	۱۱
فازهای تکمیل‌شده	۵ + اعلان‌ها
بدهی فنی مهم	۵ مورد


 در بخش «۵. مدل‌های کامل دیتابیس»، این متن رو اضافه کن (بعد از backup.BackupRecord):
markdown
### 📎 `documents.PatientDocument`

مدارک و تصاویر مربوط به مراجع.

| گروه | فیلد |
|------|------|
| اتصال | `patient` (FK → Patient)، `visit` (FK → Visit، nullable) |
| نوع | `document_type` — ۱۰ نوع (⚠️ لیست legacy — بخش بدهی فنی را ببین) |
| محتوا | `title`, `file` (upload_to=`patient_docs/%Y/%m/`), `description` |
| متادیتا | `uploaded_by`, `uploaded_at` |

**Propertyها:**
- `is_image` — چک پسوندهای تصویری
- `is_pdf` — چک `.pdf`
- `file_size_display` — بایت/کیلوبایت/مگابایت

**⚠️ نکته:** انواع مدرک شامل `tongue_top`, `tongue_bottom`, `ultrasound`,
`ct_scan`, `mri`, `ecg` هنوز از پروژه «طبیب» باقی‌مانده و برای مرکز مشاوره
بی‌معنی است. جزئیات در بخش «تله‌ها و بدهی‌های فنی».
۲) در بخش «۹. تله‌ها و بدهی‌های فنی»، این مورد رو اضافه کن:
markdown
### ⚠️ ۱۴) انواع مدرک `PatientDocument` هنوز legacy است

فیلد `document_type` در `documents.PatientDocument` هنوز شامل انواع
پزشکی است که در مرکز مشاوره معنی ندارند:

| نوع فعلی (legacy) | وضعیت پیشنهادی |
|-------------------|----------------|
| `face_photo` | 🟡 تبدیل به «عکس پرسنلی/شناسایی» یا حذف |
| `tongue_top` | ❌ حذف — مخصوص طب سنتی |
| `tongue_bottom` | ❌ حذف — مخصوص طب سنتی |
| `ultrasound` | ❌ حذف — مخصوص پزشکی |
| `ct_scan` | ❌ حذف — مخصوص پزشکی |
| `mri` | ❌ حذف — مخصوص پزشکی |
| `ecg` | ❌ حذف — مخصوص پزشکی |
| `lab` | 🟡 «آزمایش» — ممکن است در مشاوره هم لازم شود (مثلاً تیروئید) |
| `pdf` | ✅ نگه‌داشتن — عمومی |
| `other` | ✅ نگه‌داشتن — عمومی |

**پیشنهاد برای افزودن (مخصوص مشاوره):**
- `consent` — فرم رضایت‌نامه
- `psych_test` — گزارش تست روانشناسی (MMPI, PHQ-9, ...)
- `referral` — ارجاع‌نامه
- `court_letter` — نامه‌ی قضایی / دادگاه
- `school_report` — گزارش مدرسه / تحصیلی
- `insurance_form` — فرم بیمه

**راه‌حل پیشنهادی:** یک migration بنویس که مقادیر legacy را به `other` تبدیل
کند و مقادیر جدید را اضافه کند. جزئیات در فایل `AI_CONTEXT.md` ثبت شده.

بخش ۱: اضافه به PROJECT_HANDBOOK.md
۱.۱) در بخش «۹. تله‌ها و بدهی‌های فنی» — اضافه کن به لیست تله‌ها
markdown
### ⚠️ ۱۵) اعلان تغییر برنامه — الگوی دقیق (رعایت شود)

اعلان‌های تغییر برنامه از طریق `accounts/views/consultants/_helpers.py` ساخته
می‌شوند. قواعد مهم:

**۱. لینک حتماً با `reverse()` ساخته شود، نه رشته دستی:**
```python
# ❌ غلط — اگه URL عوض بشه، می‌شکنه
link = f"/accounts/consultants/{consultant.pk}/month-schedule/"

# ✅ درست
from django.urls import reverse
link = reverse("consultant_month_schedule", kwargs={"pk": consultant.pk})
۲. اعلان فقط اگه واقعاً چیزی عوض شده باشد.
از _schedule_diff_message(before, after) استفاده کن که None برمی‌گرداند
اگر تفاوتی نبود. این جلوی اعلان‌های تکراری را می‌گیرد.

۳. پیام اعلان باید دقیقاً بگوید چه چیزی عوض شد:

تغییر ساعت: شنبه ۴ مهر ۱۴۰۵ — ساعت ۰۸:۰۰–۱۴:۰۰ → ۰۸:۰۰–۱۷:۰۰

تعطیل شدن: شنبه ۴ مهر ۱۴۰۵ — تعطیل شد (قبلاً ۰۸:۰۰–۱۴:۰۰)

فعال شدن: شنبه ۴ مهر ۱۴۰۵ — فعال شد — ۰۸:۰۰–۱۶:۰۰

ساعت غیرفعال: شنبه ۴ مهر ۱۴۰۵ — ساعت غیرفعال اضافه شد: ۱۲

۴. توابع کلیدی در _helpers.py:

تابع	کاربرد
_get_effective_schedule(consultant, date)	وضعیت مؤثر روز (override یا الگوی هفتگی)
_schedule_diff_message(before, after)	تولید پیام diff (None اگر تفاوت نبود)
_notify_schedule_change(request, consultant, message)	ارسال اعلان به منشی/مدیر
_fa(text)	تبدیل ارقام به فارسی
_jalali_full(date)	۴ مهر ۱۴۰۵
_jalali_weekday(date)	شنبه
۵. هشدار: اگر URL جدیدی برای تقویم مشاور اضافه کردی، حتماً
_notify_schedule_change را بررسی کن که reverse درست داشته باشد.

text

### ۱.۲) در بخش «۱۱. Roadmap» — بخش «در حال انجام» را با این جایگزین کن

```markdown
### 🟡 در حال انجام
- اصلاحات فاز ۵
- بازنویسی `WeeklySchedule` legacy
- تغییر نام `physician` → `consultant`
- رفع برند `tabib` از لایسنس

### ✅ به‌تازگی اصلاح‌شده (changelog)

**نسخه 1.0.1 — بهبود اعلان‌های تغییر برنامه**

- 🔧 رفع باگ لینک `month-schedule` → `month` در اعلان‌ها
  (استفاده از `reverse()` به‌جای رشته دستی)
- ✨ اعلان‌ها الان diff دقیق نشان می‌دهند:
  - تغییر ساعت با فرمت `ساعت ۰۸:۰۰–۱۴:۰۰ → ۰۸:۰۰–۱۷:۰۰`
  - تعطیل/فعال شدن روز
  - تغییر ساعت‌های غیرفعال (ناهار، نماز، ...)
- 🐛 رفع مشکل اعلان تکراری — اگر چیزی عوض نشده باشد، اعلانی نمی‌رود
- 📦 توابع کمکی جدید در `_helpers.py`:
  `_get_effective_schedule`, `_schedule_diff_message`, `_fa`
- 📝 ارقام در پیام‌ها به فارسی تبدیل می‌شوند
۱.۳) یک بخش جدید به آخر فایل اضافه کن (قبل از ## 📌 پایان)
markdown
## ۱۳. Change Log

> تاریخچه‌ی تغییرات مهم پروژه. هر تغییر مهم اینجا ثبت شود.

### 1.0.1 — ۱۴۰۵/۰۷/۰۷

**موضوع:** بهبود سیستم اعلان تغییر برنامه

**فایل‌های تغییر‌یافته:**
- `accounts/views/consultants/_helpers.py` — بازنویسی کامل
- `accounts/views/consultants/api.py` — بازنویسی کامل

**تغییرات:**
- رفع باگ URL `month-schedule` → `month`
- پیام اعلان با diff دقیق
- حل مشکل اعلان تکراری
- توابع جدید: `_get_effective_schedule`, `_schedule_diff_message`, `_fa`
- تبدیل ارقام به فارسی در پیام‌ها

**نکته برای توسعه‌دهنده آینده:** اگر روی `_notify_schedule_change` تغییر دادی،
حتماً تست کن که با `reverse()` لینک ساخته می‌شود و diff قبل/بعد درست کار می‌کند.

---

### 1.0.0 — شروع پروژه

منشعب از «طبیب». ۱۳ اپ، ۵ فاز تکمیل‌شده.
📄 بخش ۲: اضافه به AI_CONTEXT.md
۲.۱) در بخش «۵. Core Concepts»، بعد از 5.13 Notifications، اضافه کن
markdown
### 5.21 Schedule Notification Helpers

توابع کلیدی در `accounts/views/consultants/_helpers.py`:

```python
_get_effective_schedule(consultant, date)  # dict: {is_active, start, end, blocked_hours, source}
_schedule_diff_message(before, after)      # str | None
_notify_schedule_change(request, consultant, message)
_fa(text)                                  # تبدیل به ارقام فارسی
الگوی استفاده در api_save_day_schedule:

python
# ۱. قبل
before_state = _get_effective_schedule(consultant, target_date)

# ۲. تغییر (delete + create override)

# ۳. بعد
after_state = _get_effective_schedule(consultant, target_date)

# ۴. diff
diff = _schedule_diff_message(before_state, after_state)
if diff:
    message = _fa(f"{day_label} — {diff}")
    _notify_schedule_change(request, consultant, message)
قواعد طلایی:

اعلان فقط وقتی diff is not None

لینک همیشه با reverse("consultant_month_schedule", kwargs={"pk": ...})

پیام حتماً شامل روز و نوع تغییر باشه

ارقام با _fa() به فارسی تبدیل بشن

text

### ۲.۲) در بخش «۹. Do's and Don'ts»، اضافه کن

### ✅ باید
- اعلان تغییر برنامه حتماً با `_notify_schedule_change` (که `reverse` دارد)
- قبل از اعلان، با `_schedule_diff_message` چک کن که واقعاً تغییری هست
- پیام‌های کاربرپسند با `_fa()` و `_jalali_full()` بساز

### ❌ نباید
- لینک اعلان رو دستی (`f"/accounts/..."`) بسازی — `reverse` استفاده کن
- بدون چک کردن diff، اعلان بفرستی — باعث اعلان تکراری می‌شه

### ۲.۳) در بخش «۱۰. Quick Reference» → جدول خطاهای رایج، این خطوط رو اضافه کن

| خطا | راه‌حل |
|-----|--------|
| `NoReverseMatch: consultant_month_schedule` | `accounts/urls.py` رو چک کن — نام URL باید `consultant_month_schedule` باشد |
| اعلان‌های قدیمی با لینک خراب | `Notification.objects.filter(link__contains="month-schedule").delete()` |
| اعلان تکراری | `_schedule_diff_message` قبل از `_notify_schedule_change` |

---

## 🎯 بعد از اضافه کردن

```powershell
git add -A
git commit -m "docs: به‌روزرسانی اسناد با بهبود سیستم اعلان تغییر برنامه (v1.0.1)"
git push origin master
