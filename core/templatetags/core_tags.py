from django import template
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def truncate_url(url, length=50):
    """Truncate a URL for display."""
    if len(url) <= length:
        return url
    return url[:length] + '...'


@register.filter
def click_badge_color(count):
    """Return a Tailwind color class based on click count."""
    if count == 0:
        return 'bg-gray-100 text-gray-600'
    if count < 10:
        return 'bg-blue-100 text-blue-700'
    if count < 100:
        return 'bg-green-100 text-green-700'
    if count < 1000:
        return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'


@register.filter
def short_timesince(value):
    """Return a short version of timesince (e.g., '2d ago')."""
    try:
        ts = timesince(value)
        first_part = ts.split(',')[0].strip()
        return f"{first_part} ago"
    except Exception:
        return ''
