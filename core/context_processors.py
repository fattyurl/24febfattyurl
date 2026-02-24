from django.core.cache import cache
def site_stats(request):
    stats = cache.get('site_stats')
    if stats is None:
        from .models import Link
        from django.utils import timezone
        today = timezone.now().date()
        stats = {
            'total_links': Link.objects.count(),
            'links_today': Link.objects.filter(created_at__date=today).count(),
        }
        cache.set('site_stats', stats, 300)  # Cache 5 minutes
    return {
        'site_stats': stats,
        'site_url': (
            f"{request.scheme}://{request.site.domain}"
            if getattr(request, 'site', None) and getattr(request.site, 'domain', None)
            else request.build_absolute_uri('/').rstrip('/')
        ),
    }
