"""تگ‌های قالبی برای بررسی ماژول‌های فعال."""
from django import template
from licensing.models import License

register = template.Library()


@register.filter
def has_feature(user, feature_name):
    """آیا ماژول فعاله؟"""
    return License.feature_enabled(feature_name)


@register.simple_tag
def current_license():
    """لایسنس فعلی."""
    return License.get_current()