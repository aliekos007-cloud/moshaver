/* ==================================================
   مشاور — مودال‌های تأیید و پرداخت
   ================================================== */

// ==================================================
// Confirm Modal
// ==================================================
function showConfirm(options) {
    return new Promise(function(resolve) {
        var opts = typeof options === 'string'
            ? { message: options }
            : (options || {});

        var overlay   = document.getElementById('confirmOverlay');
        var iconEl    = document.getElementById('confirmIcon');
        var titleEl   = document.getElementById('confirmTitle');
        var msgEl     = document.getElementById('confirmMessage');
        var okBtn     = document.getElementById('confirmOk');
        var cancelBtn = document.getElementById('confirmCancel');

        var type = opts.type || 'default';
        var iconMap = {
            default: 'bi-question-circle',
            danger:  'bi-exclamation-triangle-fill',
            warning: 'bi-exclamation-triangle-fill',
            success: 'bi-check-circle-fill',
        };
        iconEl.className = 'confirm-icon ' + type;
        iconEl.innerHTML = '<i class="bi ' + (iconMap[type] || iconMap.default) + '"></i>';

        titleEl.textContent = opts.title || (type === 'danger' ? 'هشدار' : 'تأیید');
        msgEl.textContent = opts.message || 'آیا مطمئن هستید؟';
        okBtn.textContent = opts.okText || 'تأیید';
        cancelBtn.textContent = opts.cancelText || 'انصراف';
        okBtn.className = 'btn ' + (type === 'danger' ? 'btn-danger' : 'btn-primary');

        overlay.style.display = 'flex';
        requestAnimationFrame(function() { overlay.classList.add('show'); });

        function cleanup() {
            overlay.classList.remove('show');
            setTimeout(function() { overlay.style.display = 'none'; }, 200);
            okBtn.removeEventListener('click', onOk);
            cancelBtn.removeEventListener('click', onCancel);
            overlay.removeEventListener('click', onOverlayClick);
            document.removeEventListener('keydown', onKey);
        }

        function onOk()     { cleanup(); resolve(true); }
        function onCancel() { cleanup(); resolve(false); }
        function onOverlayClick(e) { if (e.target === overlay) onCancel(); }
        function onKey(e) {
            if (e.key === 'Escape') onCancel();
            if (e.key === 'Enter')  onOk();
        }

        okBtn.addEventListener('click', onOk);
        cancelBtn.addEventListener('click', onCancel);
        overlay.addEventListener('click', onOverlayClick);
        document.addEventListener('keydown', onKey);

        setTimeout(function() { okBtn.focus(); }, 100);
    });
}

// ==================================================
// Payment Modal
// ==================================================
var FA_DIGITS_PM = "۰۱۲۳۴۵۶۷۸۹";
var EN_DIGITS_PM = "0123456789";

function _toEnDigitsPM(str) {
    return String(str)
        .replace(/[۰-۹]/g, function(d) { return EN_DIGITS_PM[FA_DIGITS_PM.indexOf(d)]; })
        .replace(/[^\d]/g, '');
}

function _toFaDigitsPM(str) {
    return String(str).replace(/\d/g, function(d) { return FA_DIGITS_PM[d]; });
}

function _formatFaMoney(num) {
    if (!num || isNaN(num)) return "۰";
    return _toFaDigitsPM(Number(num).toLocaleString('en-US')).replace(/,/g, '٬');
}

function showPaymentModal(options) {
    return new Promise(function(resolve) {
        var opts = options || {};
        var totalAmount = parseInt(opts.amount || 0);
        var clientName = opts.clientName || '';
        var defaultMethod = opts.defaultMethod || 'cash';

        var overlay = document.getElementById('paymentOverlay');
        var clientNameEl = document.getElementById('paymentClientName');
        var totalAmountEl = document.getElementById('paymentTotalAmount');
        var amountInput = document.getElementById('paymentAmountInput');
        var remainingBox = document.getElementById('paymentRemaining');
        var remainingAmountEl = document.getElementById('paymentRemainingAmount');
        var noteInput = document.getElementById('paymentNote');
        var submitBtn = document.getElementById('paymentSubmit');
        var cancelBtn = document.getElementById('paymentCancel');
        var methodBtns = document.querySelectorAll('#paymentMethods .payment-method-btn');
        var quickBtns = document.querySelectorAll('#quickAmounts .quick-amount-btn');

        var selectedMethod = defaultMethod;

        clientNameEl.textContent = clientName;
        totalAmountEl.textContent = _formatFaMoney(totalAmount);
        amountInput.value = _formatFaMoney(totalAmount);
        noteInput.value = '';
        remainingBox.classList.remove('show');

        methodBtns.forEach(function(btn) {
            btn.classList.toggle('active', btn.dataset.method === selectedMethod);
        });

        function updateRemaining() {
            var paid = parseInt(_toEnDigitsPM(amountInput.value)) || 0;
            var remaining = totalAmount - paid;
            if (remaining > 0) {
                remainingAmountEl.textContent = _formatFaMoney(remaining);
                remainingBox.classList.add('show');
            } else {
                remainingBox.classList.remove('show');
            }
        }
        updateRemaining();

        amountInput.addEventListener('input', function() {
            var raw = _toEnDigitsPM(this.value);
            if (!raw) {
                this.value = '';
                updateRemaining();
                return;
            }
            var num = parseInt(raw);
            this.value = _formatFaMoney(num);
            updateRemaining();
        });

        quickBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                var percent = parseInt(this.dataset.percent);
                var amount = Math.round(totalAmount * percent / 100);
                amountInput.value = _formatFaMoney(amount);

                quickBtns.forEach(function(b) { b.classList.remove('active'); });
                this.classList.add('active');

                updateRemaining();
            });
        });

        var fullBtn = document.querySelector('#quickAmounts .quick-amount-btn[data-percent="100"]');
        if (fullBtn) fullBtn.classList.add('active');

        methodBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                methodBtns.forEach(function(b) { b.classList.remove('active'); });
                this.classList.add('active');
                selectedMethod = this.dataset.method;
            });
        });

        overlay.style.display = 'flex';
        requestAnimationFrame(function() {
            overlay.classList.add('show');
            setTimeout(function() { amountInput.focus(); amountInput.select(); }, 200);
        });

        function cleanup() {
            overlay.classList.remove('show');
            setTimeout(function() { overlay.style.display = 'none'; }, 200);
            submitBtn.removeEventListener('click', onSubmit);
            cancelBtn.removeEventListener('click', onCancel);
            overlay.removeEventListener('click', onOverlayClick);
            document.removeEventListener('keydown', onKey);
        }

        function onSubmit() {
            var amount = parseInt(_toEnDigitsPM(amountInput.value)) || 0;

            if (amount <= 0) {
                showToast('مبلغ پرداخت باید بزرگ‌تر از صفر باشد.', 'error');
                amountInput.focus();
                return;
            }

            if (amount > totalAmount) {
                showToast('مبلغ پرداختی بیشتر از مبلغ قابل پرداخت است.', 'error');
                amountInput.focus();
                return;
            }

            cleanup();
            resolve({
                amount: amount,
                method: selectedMethod,
                note: noteInput.value.trim(),
            });
        }

        function onCancel() { cleanup(); resolve(null); }
        function onOverlayClick(e) { if (e.target === overlay) onCancel(); }
        function onKey(e) {
            if (e.key === 'Escape') onCancel();
        }

        submitBtn.addEventListener('click', onSubmit);
        cancelBtn.addEventListener('click', onCancel);
        overlay.addEventListener('click', onOverlayClick);
        document.addEventListener('keydown', onKey);
    });
}