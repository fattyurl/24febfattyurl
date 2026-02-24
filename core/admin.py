from django.contrib import admin
from .models import Link, Click, UserProfile


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ['short_code', 'custom_slug', 'original_url_truncated', 'user', 'click_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['short_code', 'custom_slug', 'original_url', 'title']
    date_hierarchy = 'created_at'
    readonly_fields = ['short_code', 'click_count', 'created_at', 'updated_at']

    def original_url_truncated(self, obj):
        url = obj.original_url
        return url[:80] + '...' if len(url) > 80 else url
    original_url_truncated.short_description = 'Original URL'


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ['link', 'clicked_at', 'country', 'city', 'device_type', 'browser', 'os']
    list_filter = ['device_type', 'browser', 'os', 'country']
    search_fields = ['link__short_code', 'link__custom_slug', 'country', 'city']
    date_hierarchy = 'clicked_at'
    readonly_fields = ['link', 'clicked_at', 'referrer', 'user_agent', 'country', 'city', 'device_type', 'browser', 'os', 'ip_hash']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'api_key_prefix', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['api_key_hash', 'created_at']
