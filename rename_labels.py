from pathlib import Path

ROOT = Path(".")
EXCLUDE_DIRS = {
    "venv", "__pycache__", ".git", "migrations",
    "node_modules", "media", "staticfiles", "logs", "backups",
}

REPLACEMENTS = [
    ("مراجع جدید", "مراجع جدید"),
    ("ثبت مراجع", "ثبت مراجع"),
    ("آخرین مراجعین", "آخرین مراجعین"),
    ("کل مراجعین", "کل مراجعین"),
    ("تعداد کل مراجعین", "تعداد کل مراجعین"),
    ("لیست مراجعین", "لیست مراجعین"),
    ("پروفایل مراجع", "پروفایل مراجع"),
    ("پروندهٔ مراجع", "پروندهٔ مراجع"),
    ("اطلاعات مراجع", "اطلاعات مراجع"),
    ("نام مراجع", "نام مراجع"),
    ("شماره پروندهٔ مراجع", "شماره پروندهٔ مراجع"),
    ("مراجعین", "مراجعین"),
    ("مراجع", "مراجع"),
]

count = 0
for path in ROOT.rglob("*"):
    if any(part in EXCLUDE_DIRS for part in path.parts):
        continue
    if not path.is_file():
        continue
    if path.suffix not in (".py", ".html", ".txt", ".md"):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        continue
    original = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        count += 1
        print(f"OK: {path}")

print(f"\n{count} file(s) updated.")