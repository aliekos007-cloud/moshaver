from licensing.decorators import feature_required
import os
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404

from accounts.decorators import manager_required
from audit.models import log_action
from .models import BackupRecord
from .services import create_backup, restore_backup, delete_backup_file, BACKUP_DIR

@feature_required("backup")
@manager_required
def backup_list(request):
    records = BackupRecord.objects.select_related("created_by").all()[:50]
    return render(request, "backup/list.html", {
        "records": records,
        "backup_dir": str(BACKUP_DIR),
    })


@feature_required("backup")
@manager_required
def backup_create(request):
    if request.method == "POST":
        record = create_backup(user=request.user)
        if record.status == "success":
            log_action(
                request, "backup",
                description=f"ساخت پشتیبان: {record.file_name} ({record.size_display})",
            )
            messages.success(request, f"پشتیبان با موفقیت ساخته شد: {record.file_name}")
        else:
            log_action(
                request, "backup",
                description=f"خطا در پشتیبان‌گیری: {record.note}",
            )
            messages.error(request, f"خطا در پشتیبان‌گیری: {record.note}")
    return redirect("backup_list")


@feature_required("backup")
@manager_required
def backup_download(request, pk):
    record = get_object_or_404(BackupRecord, pk=pk)
    file_path = BACKUP_DIR / record.file_name
    if not file_path.exists():
        raise Http404("فایل پشتیبان پیدا نشد.")
    log_action(
        request, "export", record,
        description=f"دانلود پشتیبان: {record.file_name}",
    )
    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=record.file_name,
    )


@feature_required("backup")
@manager_required
def backup_delete(request, pk):
    record = get_object_or_404(BackupRecord, pk=pk)
    if request.method == "POST":
        file_name = record.file_name
        delete_backup_file(file_name)
        record.delete()
        log_action(
            request, "delete",
            description=f"حذف پشتیبان: {file_name}",
        )
        messages.success(request, "پشتیبان حذف شد.")
    return redirect("backup_list")


@feature_required("backup")
@manager_required
def backup_restore(request, pk):
    record = get_object_or_404(BackupRecord, pk=pk)
    if request.method == "POST":
        file_path = BACKUP_DIR / record.file_name
        try:
            emergency = restore_backup(str(file_path))
            log_action(
                request, "restore", record,
                description=f"بازیابی از پشتیبان: {record.file_name} (پشتیبان اضطراری: {emergency})",
            )
            messages.warning(
                request,
                f"بازیابی انجام شد. یک پشتیبان اضطراری از وضعیت قبلی ذخیره شد: {emergency} "
                f"⚠️ لطفاً سرور را restart کنید."
            )
        except Exception as e:
            log_action(
                request, "restore", record,
                description=f"خطا در بازیابی: {e}",
            )
            messages.error(request, f"خطا در بازیابی: {e}")
    return redirect("backup_list")