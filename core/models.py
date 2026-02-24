import secrets
import string

from django.conf import settings
from django.db import models
from django.contrib.sites.models import Site


def get_site_base_url(request=None):
    if request is not None:
        site = getattr(request, 'site', None)
        if site is not None and getattr(site, 'domain', None):
            return f"{request.scheme}://{site.domain}"
        return request.build_absolute_uri('/').rstrip('/')

    site = Site.objects.get_current()
    if site is not None and getattr(site, 'domain', None):
        return f"https://{site.domain}"
    return ''


def generate_short_code():
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(7))
        if not Link.objects.filter(short_code=code).exists():
            return code


class Link(models.Model):
    short_code = models.CharField(max_length=10, unique=True, db_index=True, default=generate_short_code)
    custom_slug = models.CharField(max_length=100, unique=True, null=True, blank=True, db_index=True)
    original_url = models.URLField(max_length=2048)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='links', db_index=True,
    )
    title = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    click_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_short_url()} -> {self.original_url[:60]}"

    def get_short_url(self, request=None):
        slug = self.custom_slug or self.short_code
        base_url = get_site_base_url(request)
        if base_url:
            return f"{base_url.rstrip('/')}/{slug}"
        return f"/{slug}"

    def get_display_code(self):
        return self.custom_slug or self.short_code


class Click(models.Model):
    link = models.ForeignKey(Link, on_delete=models.CASCADE, related_name='clicks', db_index=True)
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    referrer = models.URLField(max_length=2048, blank=True, default='')
    user_agent = models.TextField(blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    device_type = models.CharField(max_length=20, blank=True, default='')
    browser = models.CharField(max_length=50, blank=True, default='')
    os = models.CharField(max_length=50, blank=True, default='')
    ip_hash = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['link', 'clicked_at']),
        ]

    def __str__(self):
        return f"Click on {self.link.get_display_code()} at {self.clicked_at}"


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    api_key_hash = models.CharField(max_length=64, blank=True, default='')
    api_key_prefix = models.CharField(max_length=8, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile for {self.user.email}"
