import hashlib
import re
from urllib.parse import urlparse

from user_agents import parse as parse_ua

RESERVED_SLUGS = {
    'api', 'admin', 'accounts', 'account', 'dashboard', 'shorten', 'check-slug',
    'migrate', 'contact', 'qr', 'about', 'terms', 'privacy', 'promise',
    'bitly-alternative', 'tinyurl-alternative', 'pricing', 'help', 'docs',
    'support', 'blog', 'login', 'signup', 'logout', 'settings', 'static', 'media',
    'robots', 'favicon', 'favicon.ico', 'sitemap', 'home',
    'api-stats', 'api-health', 'api-v1',
}

SLUG_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$')


def validate_url(url):
    """Validate URL is HTTP/HTTPS, not localhost, not recursive."""
    if not url:
        return False, "URL is required."
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format."
    if parsed.scheme not in ('http', 'https'):
        return False, "Only HTTP and HTTPS URLs are allowed."
    hostname = parsed.hostname or ''
    if hostname in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
        return False, "Localhost URLs are not allowed."
    if 'fattyurl.com' in hostname or 'fattyurl' in hostname:
        return False, "Cannot shorten FattyURL links."
    return True, None


def validate_slug(slug):
    """Validate custom slug format and availability."""
    if not slug:
        return True, None
    slug = slug.strip()
    slug_lower = slug.lower()

    if slug_lower in RESERVED_SLUGS:
        return False, "This slug is reserved."
    if len(slug) < 6:
        return False, "Slug must be at least 6 characters."
    if len(slug) > 100:
        return False, "Slug must be 100 characters or fewer."
    if not SLUG_PATTERN.match(slug):
        return False, "Slug can only contain letters, numbers, and hyphens."
    return True, None


def parse_user_agent(ua_string):
    """Parse user agent string into device type, browser, and OS."""
    if not ua_string:
        return {'device_type': 'unknown', 'browser': 'Unknown', 'os': 'Unknown'}
    ua = parse_ua(ua_string)
    if ua.is_mobile:
        device_type = 'mobile'
    elif ua.is_tablet:
        device_type = 'tablet'
    elif ua.is_pc:
        device_type = 'desktop'
    elif ua.is_bot:
        device_type = 'bot'
    else:
        device_type = 'unknown'
    browser = ua.browser.family or 'Unknown'
    os_name = ua.os.family or 'Unknown'
    return {'device_type': device_type, 'browser': browser, 'os': os_name}


def hash_ip(ip_address):
    """SHA-256 hash of IP address. Never store raw IPs."""
    if not ip_address:
        return ''
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()


def get_client_ip(request):
    """Extract client IP from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def get_geo_from_request(request):
    """Extract geo info from CDN headers (Cloudflare, Vercel)."""
    country = (
        request.META.get('HTTP_CF_IPCOUNTRY')
        or request.META.get('HTTP_X_VERCEL_IP_COUNTRY')
        or ''
    )
    city = (
        request.META.get('HTTP_CF_IPCITY')
        or request.META.get('HTTP_X_VERCEL_IP_CITY')
        or ''
    )
    return {'country': country, 'city': city}
