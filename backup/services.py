"""سرویس پشتیبان‌گیری و بازیابی."""
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

import jdatetime
from django.conf import settings

BACKUP_DIR = Path(settings.BASE_DIR) / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


def create_backup(user=None, note=""):
    """یک فایل zip از دیتابیس و مدیا می‌سازد."""
    from .models import BackupRecord

    today = jdatetime.datetime.now()
    timestamp = today.strftime("%Y%m%d_%H%M%S")
    file_name = f"tabib_backup_{timestamp}.zip"
    file_path = BACKUP_DIR / file_name

    try:
        with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # دیتابیس SQLite
            db_path = settings.DATABASES["default"]["NAME"]
            if os.path.exists(db_path):
                zf.write(db_path, "db.sqlite3")

            # پوشه‌ی media (اگر وجود دارد)
            media_root = Path(settings.MEDIA_ROOT)
            if media_root.exists():
                for root, _, files in os.walk(media_root):
                    for f in files:
                        full = Path(root) / f
                        rel = full.relative_to(media_root)
                        zf.write(full, f"media/{rel}")

        size = file_path.stat().st_size
        record = BackupRecord.objects.create(
            file_name=file_name,
            file_size=size,
            created_by=user,
            status="success",
            note=note or "پشتیبان کامل (دیتابیس + رسانه)",
        )
        return record

    except Exception as e:
        record = BackupRecord.objects.create(
            file_name=file_name,
            file_size=0,
            created_by=user,
            status="failed",
            note=f"خطا: {e}",
        )
        return record


def restore_backup(file_path):
    """بازیابی از فایل zip. توجه: Django باید restart شود."""
    if not os.path.exists(file_path):
        raise FileNotFoundError("فایل پشتیبان پیدا نشد.")

    # ۱) پشتیبان اضطراری از وضعیت فعلی
    emergency_name = f"emergency_before_restore_{datetime.now():%Y%m%d_%H%M%S}.zip"
    emergency_path = BACKUP_DIR / emergency_name
    db_path = settings.DATABASES["default"]["NAME"]

    with zipfile.ZipFile(emergency_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(db_path):
            zf.write(db_path, "db.sqlite3")

    # ۲) استخراج فایل پشتیبان جدید در پوشه‌ی موقت
    extract_dir = BACKUP_DIR / "_restore_temp"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir()

    with zipfile.ZipFile(file_path, "r") as zf:
        zf.extractall(extract_dir)

    # ۳) کپی فایل‌ها روی مقصد
    new_db = extract_dir / "db.sqlite3"
    if new_db.exists():
        shutil.copy2(new_db, db_path)

    media_src = extract_dir / "media"
    if media_src.exists():
        media_dst = Path(settings.MEDIA_ROOT)
        media_dst.mkdir(exist_ok=True)
        for item in media_src.iterdir():
            target = media_dst / item.name
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    # ۴) پاکسازی
    shutil.rmtree(extract_dir)

    return emergency_name


def delete_backup_file(file_name):
    """حذف فیزیکی فایل پشتیبان."""
    path = BACKUP_DIR / file_name
    if path.exists():
        path.unlink()
        return True
    return False


def list_backup_files():
    """لیست فایل‌های پشتیبان روی دیسک."""
    if not BACKUP_DIR.exists():
        return []
    files = []
    for f in sorted(BACKUP_DIR.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True):
        files.append({
            "name": f.name,
            "size": f.stat().st_size,
            "mtime": datetime.fromtimestamp(f.stat().st_mtime),
        })
    return files