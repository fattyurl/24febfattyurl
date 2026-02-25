from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.http import Http404, HttpResponse
from django.contrib.staticfiles.storage import staticfiles_storage
from core import views
from core.sitemaps import StaticViewSitemap

handler404 = 'core.views.custom_404'

def serve_favicon_ico(request):
    if not staticfiles_storage.exists('favicon.ico'):
        raise Http404('favicon.ico not found')

    with staticfiles_storage.open('favicon.ico', 'rb') as favicon_file:
        return HttpResponse(favicon_file.read(), content_type='image/x-icon')


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': {'static': StaticViewSitemap}},
        name='sitemap',
    ),
    # Favicon
    path('favicon.ico', serve_favicon_ico, name='favicon_ico'),

    # Auth (django-allauth)
    path('accounts/', include('allauth.urls')),

    # Homepage
    path('', views.home, name='home'),

    # Shortener endpoints
    path('shorten/', views.shorten_url, name='shorten_url'),
    path('check-slug/', views.check_slug, name='check_slug'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/link/<int:pk>/', views.link_analytics, name='link_analytics'),
    path('dashboard/link/<int:pk>/edit/', views.edit_link, name='edit_link'),
    path('dashboard/link/<int:pk>/delete/', views.delete_link, name='delete_link'),
    path('dashboard/export/', views.export_links_csv, name='export_links_csv'),

    # QR Code
    path('qr/', views.qr_generator, name='qr_generator'),
    path('qr/generate/', views.generate_qr, name='generate_qr'),

    # SEO & Marketing pages
    path('bitly-alternative/', views.bitly_alternative, name='bitly_alternative'),
    path('promise/', views.promise_page, name='promise_page'),
    path('about/', views.about_page, name='about_page'),
    path('privacy/', views.privacy_page, name='privacy_page'),
    path('terms/', views.terms_page, name='terms_page'),
    path('contact/', views.contact_page, name='contact_page'),

    # Migration
    path('migrate/', views.migrate_page, name='migrate_page'),

    # API
    path('api/stats', views.public_stats, name='public_stats'),
    path('api/health', views.health_check, name='health_check'),
    path('api/v1/', include('api.urls')),

    # MUST BE LAST — catch-all redirect
    path('<str:code>/', views.redirect_short_url, name='redirect_short_url'),
]

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
