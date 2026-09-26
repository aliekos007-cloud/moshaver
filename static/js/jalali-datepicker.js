/* ==================================================
   مشاور — تقویم شمسی خودکار
   ================================================== */
(function() {
    'use strict';

    if (typeof window.jQuery === 'undefined') return;
    if (typeof window.persianDate === 'undefined') return;

    var $ = window.jQuery;
    var FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹";

    function toFaDigits(str) {
        return String(str).replace(/\d/g, function(d) { return FA_DIGITS[d]; });
    }

    function convertDateInput(input) {
        var $original = $(input);

        if ($original.data('jalali-done')) return;
        $original.data('jalali-done', true);

        var originalClass = $original.attr('class') || 'form-control';
        var originalId = $original.attr('id') || '';
        var originalValue = $original.val() || '';
        var isRequired = $original.prop('required');

        $original.attr('type', 'hidden');

        var $display = $('<input>', {
            type: 'text',
            class: originalClass + ' jalali-date-display',
            placeholder: 'مثلاً: ۱۴۰۵/۰۷/۰۳',
            readonly: true,
            autocomplete: 'off',
            dir: 'ltr',
        });

        if (originalId) $display.attr('id', originalId + '_display');
        if (isRequired) $display.attr('required', 'required');

        $original.after($display);

        // ===== تبدیل مقدار میلادی به شمسی =====
        function toJalaliString(value) {
            if (!value) return '';
            var parts = value.split('-');
            if (parts.length !== 3) return '';

            var g = new Date(
                parseInt(parts[0]),
                parseInt(parts[1]) - 1,
                parseInt(parts[2])
            );
            if (isNaN(g.getTime())) return '';

            var pd = new window.persianDate(g);
            return toFaDigits(pd.format('YYYY/MM/DD'));
        }

        // ===== راه‌اندازی picker =====
        $display.persianDatepicker({
            format: 'YYYY/MM/DD',
            initialValue: false,
            autoClose: true,
            persianDigit: true,
            observer: false,
            position: 'auto',
            calendar: {
                persian: {
                    locale: 'fa',
                    leapYearMode: 'algorithmic',
                }
            },
            toolbox: {
                calendarSwitch: { enabled: false }
            },
            navigator: {
                scroll: { enabled: false }
            },
            onSelect: function(unix) {
                var pd = new window.persianDate(unix);
                var gy = pd.year();
                var gm = pd.month();
                var gd = pd.date();
                var iso = gy + '-' + String(gm).padStart(2, '0') + '-' + String(gd).padStart(2, '0');
                $original.val(iso);
                $display.val(toFaDigits(pd.format('YYYY/MM/DD')));
                $original.trigger('change');
            }
        });

        // ===== ✅ بعد از راه‌اندازی، مقدار رو دستی ست کن =====
        var jalaliStr = toJalaliString(originalValue);
        if (jalaliStr) {
            $display.val(jalaliStr);

            // پاک‌سازی هر state داخل picker
            setTimeout(function() {
                $display.val(jalaliStr);
            }, 50);
        }

        // باز کردن با کلیک
        $display.on('focus click', function() {
            var dp = $display.data('datepicker');
            if (dp) dp.show();
        });
    }

    function initAll() {
        document.querySelectorAll('input[type="date"]').forEach(convertDateInput);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }

    var observer = new MutationObserver(function(mutations) {
        var shouldInit = false;
        mutations.forEach(function(m) {
            m.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) {
                    if (node.matches && node.matches('input[type="date"]')) shouldInit = true;
                    if (node.querySelectorAll && node.querySelectorAll('input[type="date"]').length) shouldInit = true;
                }
            });
        });
        if (shouldInit) initAll();
    });

    document.addEventListener('DOMContentLoaded', function() {
        observer.observe(document.body, { childList: true, subtree: true });
    });
})();