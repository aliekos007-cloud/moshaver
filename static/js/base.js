/* ==================================================
   مشاور — اسکریپت اصلی
   ================================================== */

// ==================================================
// سایدبار
// ==================================================
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.querySelector('.sidebar-overlay').classList.toggle('active');
}

// ==================================================
// میان‌برهای کیبورد
// ==================================================
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        var sb = document.getElementById('sidebar');
        if (sb && sb.classList.contains('open')) toggleSidebar();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        var searchInput = document.querySelector('.global-search input');
        if (searchInput) searchInput.focus();
    }
});

// ==================================================
// Toast
// ==================================================
var TOAST_ICONS = {
    success: 'bi-check-circle-fill',
    error: 'bi-x-circle-fill',
    danger: 'bi-x-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info: 'bi-info-circle-fill',
    debug: 'bi-bug-fill'
};

function showToast(text, tags) {
    tags = (tags || 'info').trim();
    var container = document.getElementById('toastContainer');
    var icon = TOAST_ICONS[tags] || 'bi-info-circle-fill';
    var el = document.createElement('div');
    el.className = 'toast-item toast-' + tags;
    el.innerHTML = ''
        + '<div class="toast-icon"><i class="bi ' + icon + '"></i></div>'
        + '<div class="toast-body">' + text + '</div>'
        + '<button class="toast-close" onclick="removeToast(this)"><i class="bi bi-x-lg"></i></button>'
        + '<div class="toast-progress"></div>';
    container.appendChild(el);
    setTimeout(function() { if (el.parentNode) removeToastEl(el); }, 4500);
}

function removeToast(btn) {
    var el = btn.closest('.toast-item');
    if (el) removeToastEl(el);
}

function removeToastEl(el) {
    el.classList.add('removing');
    setTimeout(function() { if (el.parentNode) el.parentNode.removeChild(el); }, 300);
}
function getCsrf() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el) return el.value;
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
}

// نمایش پیام‌های Django
document.addEventListener('DOMContentLoaded', function() {
    var msgScript = document.getElementById('django-messages');
    if (msgScript) {
        try {
            var msgs = JSON.parse(msgScript.textContent);
            msgs.forEach(function(m, i) {
                setTimeout(function() { showToast(m.text, m.tags); }, i * 150);
            });
        } catch (e) {
            console.error('خطا در پیام‌ها:', e);
        }
    }
});
/* ==================================================
   Notifications
   ================================================== */
let notifOpen = false;
let notifPollInterval = null;

function toggleNotifications() {
    var dropdown = document.getElementById('notifDropdown');
    if (!dropdown) return;

    notifOpen = !notifOpen;

    if (notifOpen) {
        dropdown.classList.add('show');
        loadNotifications();
    } else {
        dropdown.classList.remove('show');
    }
}

function closeNotifications() {
    var dropdown = document.getElementById('notifDropdown');
    if (dropdown) dropdown.classList.remove('show');
    notifOpen = false;
}

document.addEventListener('click', function(e) {
    var wrapper = document.querySelector('.notif-wrapper');
    if (wrapper && !wrapper.contains(e.target)) {
        closeNotifications();
    }
});

async function loadNotifications() {
    var body = document.getElementById('notifBody');
    if (!body) return;

    try {
        var res = await fetch('/notifications/api/list/');
        var data = await res.json();

        if (!data.ok) {
            body.innerHTML = '<div class="notif-empty"><i class="bi bi-x-circle"></i>خطا</div>';
            return;
        }

        updateNotifBadge(data.unread_count);

        if (data.notifications.length === 0) {
            body.innerHTML = '<div class="notif-empty"><i class="bi bi-bell-slash"></i>هیچ اعلانی ندارید</div>';
            return;
        }

        var html = '';
        data.notifications.forEach(function(n) {
            var iconClass = getNotifIcon(n.type);
            var unreadClass = n.is_read ? '' : 'unread';

            html += '<a href="' + (n.link || 'javascript:void(0)') + '" ' +
                    'class="notif-list-item ' + unreadClass + '" ' +
                    'onclick="markNotifRead(' + n.id + ', event)">' +
                        '<div class="icon"><i class="bi ' + iconClass + '"></i></div>' +
                        '<div class="content">' +
                            '<div class="ttl">' + n.title + '</div>' +
                            (n.message ? '<div class="msg">' + n.message + '</div>' : '') +
                            '<div class="time">' + n.created_at_relative + '</div>' +
                        '</div>' +
                    '</a>';
        });

        body.innerHTML = html;

    } catch (err) {
        console.error(err);
        body.innerHTML = '<div class="notif-empty"><i class="bi bi-x-circle"></i>خطای شبکه</div>';
    }
}

function getNotifIcon(type) {
    var map = {
        'schedule_changed': 'bi-calendar-week',
        'leave_request': 'bi-calendar-x',
        'new_session': 'bi-calendar-plus',
        'session_overdue': 'bi-exclamation-triangle',
        'payment_deferred': 'bi-cash-coin',
        'survey_response': 'bi-star',
        'system_alert': 'bi-bell',
    };
    return map[type] || 'bi-bell';
}

function updateNotifBadge(count) {
    var badge = document.getElementById('notifBadge');
    var countEl = document.getElementById('notifCount');

    if (!badge) return;

    if (count > 0) {
        badge.textContent = toFaDigitsNotif(count);
        badge.style.display = 'inline-block';
        if (countEl) countEl.textContent = toFaDigitsNotif(count);
    } else {
        badge.style.display = 'none';
        if (countEl) countEl.textContent = '۰';
    }
}

function toFaDigitsNotif(str) {
    var fa = "۰۱۲۳۴۵۶۷۸۹";
    return String(str).replace(/\d/g, function(d) { return fa[d]; });
}

async function markNotifRead(id, event) {
    event.preventDefault();
    event.stopPropagation();

    var item = event.currentTarget;

    try {
        var res = await fetch('/notifications/api/' + id + '/read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrf(),
                'Content-Type': 'application/json',
            },
        });
        var data = await res.json();

        if (data.ok) {
            item.classList.remove('unread');
            updateNotifBadge(data.unread_count);

            var link = item.getAttribute('href');
            if (link && link !== 'javascript:void(0)') {
                setTimeout(function() { window.location.href = link; }, 200);
            }
        }
    } catch (err) {
        console.error(err);
    }
}

async function markAllRead(event) {
    event.preventDefault();
    event.stopPropagation();

    try {
        var res = await fetch('/notifications/api/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrf(),
                'Content-Type': 'application/json',
            },
        });
        var data = await res.json();

        if (data.ok) {
            updateNotifBadge(0);
            document.querySelectorAll('.notif-list-item.unread').forEach(function(el) {
                el.classList.remove('unread');
            });
        }
    } catch (err) {
        console.error(err);
    }
}

async function checkUnreadCount() {
    try {
        var res = await fetch('/notifications/api/unread/');
        var data = await res.json();
        if (data.ok) {
            updateNotifBadge(data.count);
        }
    } catch (err) {
        // ساکت باش
    }
}

document.addEventListener('DOMContentLoaded', function() {
    checkUnreadCount();
    notifPollInterval = setInterval(checkUnreadCount, 30000);
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && notifOpen) {
        closeNotifications();
    }
});