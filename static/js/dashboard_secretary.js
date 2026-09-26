/* ==================================================
   مشاور — اسکریپت داشبورد عملیاتی منشی
   ================================================== */

// ==================================================
// ابزار ارقام فارسی
// ==================================================
const FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹";
function toFa(str) {
    return String(str).replace(/\d/g, d => FA_DIGITS[d]);
}

function fmtDuration(seconds) {
    if (seconds < 0) seconds = 0;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) {
        return toFa(`${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`);
    }
    return toFa(`${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`);
}

function fmtPrice(n) {
    if (!n || isNaN(n)) return '۰';
    return toFa(Number(n).toLocaleString('en-US')).replace(/,/g, '٬');
}

// ==================================================
// ساعت زنده
// ==================================================
function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    const el = document.getElementById('live-clock');
    if (el) el.textContent = toFa(`${h}:${m}:${s}`);
}
setInterval(updateClock, 1000);
updateClock();

// ==================================================
// CSRF
// ==================================================
function getCsrf() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el) return el.value;
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
}

// ==================================================
// تایمر زنده جلسات
// ==================================================
function tick() {
    document.querySelectorAll('[data-session-id]').forEach(card => {
        const startedAt = card.dataset.startedAt;
        if (!startedAt) return;

        const standardMin = parseInt(card.dataset.standardMinutes || '45');
        const graceMin    = parseInt(card.dataset.graceMinutes    || '5');
        const standardSec = standardMin * 60;
        const graceSec    = graceMin * 60;

        const basePrice   = parseInt(card.dataset.basePrice        || '0');
        const overtimeRate= parseInt(card.dataset.overtimeRate     || '0');
        const pausedSec   = parseInt(card.dataset.pausedSeconds    || '0');

        const now = Date.now();
        const start = new Date(startedAt).getTime();
        const elapsed = Math.floor((now - start) / 1000) - pausedSec;
        const remaining = standardSec - elapsed;

        const elElapsed = card.querySelector('.t-elapsed');
        const elRemaining = card.querySelector('.t-remaining');
        if (elElapsed) elElapsed.textContent = fmtDuration(elapsed);
        if (elRemaining) {
            if (remaining >= 0) {
                elRemaining.textContent = fmtDuration(remaining);
                elRemaining.parentElement.classList.remove('overtime');
            } else {
                elRemaining.textContent = '+' + fmtDuration(-remaining);
                elRemaining.parentElement.classList.add('overtime');
            }
        }

        const bar = card.querySelector('.progress-bar-live');
        if (bar) {
            let pct = (elapsed / standardSec) * 100;
            if (pct > 100) pct = 100;
            bar.style.width = pct + '%';

            let state = 'normal';
            if (elapsed > standardSec + graceSec) state = 'overtime';
            else if (elapsed > standardSec) state = 'grace';
            else if (pct > 80) state = 'ending';

            bar.dataset.state = state;
            card.dataset.state = state;
        }

        const elFee = card.querySelector('.t-fee');
        if (elFee) {
            let fee = basePrice;
            const minutes = Math.floor(elapsed / 60);
            if (minutes > standardMin + graceMin) {
                const overage = minutes - standardMin - graceMin;
                fee = basePrice + (overage * overtimeRate);
            }
            elFee.textContent = fmtPrice(fee);
        }
    });
}
setInterval(tick, 1000);
tick();

// ==================================================
// API helper
// ==================================================
async function apiCall(url, data = {}) {
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', getCsrf());
    for (const [k, v] of Object.entries(data)) {
        formData.append(k, v);
    }
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() },
        body: formData,
    });
    return await res.json();
}

// ==================================================
// عملیات جلسه
// ==================================================
async function startSession(id) {
    const ok = await showConfirm({
        type: 'success',
        title: 'شروع جلسه',
        message: 'آیا جلسه شروع شود؟ تایمر از این لحظه آغاز می‌شود.',
        okText: 'بله، شروع کن',
    });
    if (!ok) return;

    const data = await apiCall(`/records/session/${id}/start/`);
    if (data.ok) {
        showToast('جلسه شروع شد', 'success');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast(data.error || 'خطا', 'error');
    }
}

async function pauseSession(id) {
    const data = await apiCall(`/records/session/${id}/pause/`);
    if (data.ok) {
        showToast('وقفه ثبت شد', 'info');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast(data.error || 'خطا', 'error');
    }
}

async function resumeSession(id) {
    const data = await apiCall(`/records/session/${id}/resume/`);
    if (data.ok) {
        showToast('جلسه ادامه یافت', 'success');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast(data.error || 'خطا', 'error');
    }
}

async function extendSession(id, minutes) {
    const ok = await showConfirm({
        type: 'warning',
        title: 'تمدید جلسه',
        message: `آیا ${minutes} دقیقه به زمان استاندارد این جلسه اضافه شود؟`,
        okText: 'بله، تمدید کن',
    });
    if (!ok) return;

    const data = await apiCall(`/records/session/${id}/extend/`, { minutes: minutes });
    if (data.ok) {
        showToast(`${minutes} دقیقه تمدید شد`, 'success');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast(data.error || 'خطا', 'error');
    }
}

async function endSession(id) {
    const ok = await showConfirm({
        type: 'danger',
        title: 'پایان جلسه',
        message: 'آیا جلسه پایان یابد؟ مبلغ بر اساس زمان واقعی محاسبه می‌شود.',
        okText: 'بله، پایان بده',
    });
    if (!ok) return;

    const data = await apiCall(`/records/session/${id}/end/`);
    if (data.ok) {
        showToast(`جلسه تمام شد — ${data.summary.duration_minutes} دقیقه`, 'success');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast(data.error || 'خطا', 'error');
    }
}

async function paySession(id) {
    let totalAmount = 0;
    let clientName = '';

    const card = document.querySelector(`[data-session-id="${id}"]`);
    if (card) {
        const feeEl = card.querySelector('.t-fee');
        if (feeEl) {
            const feeText = feeEl.textContent.replace(/[^\d۰-۹]/g, '');
            const enDigits = feeText.replace(/[۰-۹]/g, d => "۰۱۲۳۴۵۶۷۸۹".indexOf(d));
            totalAmount = parseInt(enDigits) || 0;
        }
        const nameEl = card.querySelector('.client-line');
        if (nameEl) {
            clientName = nameEl.textContent.trim().split('—')[0].trim();
        }
    }

    if (!totalAmount) {
        showToast('مبلغ جلسه مشخص نیست.', 'error');
        return;
    }

    const result = await showPaymentModal({
        amount: totalAmount,
        clientName: clientName,
        defaultMethod: 'cash',
    });

    if (!result) return;

    const data = await apiCall(`/records/session/${id}/pay/`, {
        amount: result.amount,
        method: result.method,
        note: result.note,
    });

    if (data.ok) {
        if (data.paid.remaining > 0) {
            showToast(
                `پرداخت ${fmtPrice(result.amount)} تومان — باقی‌مانده: ${fmtPrice(data.paid.remaining)} تومان`,
                'info'
            );
        } else {
            showToast(`پرداخت ${fmtPrice(result.amount)} تومان با موفقیت ثبت شد.`, 'success');
        }
        setTimeout(() => location.reload(), 800);
    } else {
        showToast(data.error || 'خطا در ثبت پرداخت', 'error');
    }
}

async function deferPayment(id) {
    const ok = await showConfirm({
        type: 'warning',
        title: 'ثبت نسیه',
        message: 'آیا این جلسه به‌عنوان نسیه ثبت شود؟ مبلغ به بدهی مراجع اضافه می‌شود.',
        okText: 'بله، نسیه کن',
    });
    if (!ok) return;

    const data = await apiCall(`/records/session/${id}/defer/`, {});
    if (data.ok) {
        showToast('جلسه به‌عنوان نسیه ثبت شد', 'warning');
        setTimeout(() => location.reload(), 500);
    } else {
        showToast(data.error || 'خطا', 'error');
    }
}

// ==================================================
// بروزرسانی خودکار
// ==================================================
setInterval(() => {
    if (document.visibilityState === 'visible') {
        location.reload();
    }
}, 15000);