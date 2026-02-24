import csv
import io
import json
import threading
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Count, F, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .forms import ShortenerForm, LinkEditForm
from .models import Link, Click
from .utils import (
    parse_user_agent, hash_ip, get_client_ip, get_geo_from_request,
    validate_slug,
)


# ---------------------
# Homepage & Shortening
# ---------------------

def home(request):
    form = ShortenerForm()
    return render(request, 'home.html', {'form': form})


@require_POST
def shorten_url(request):
    form = ShortenerForm(request.POST)
    if form.is_valid():
        link = Link(
            original_url=form.cleaned_data['url'],
            user=request.user if request.user.is_authenticated else None,
        )
        custom_slug = form.cleaned_data.get('custom_slug')
        if custom_slug:
            link.custom_slug = custom_slug
        link.save()
        return render(request, 'partials/shorten_result.html', {
            'link': link,
            'is_authenticated': request.user.is_authenticated,
        })
    return render(request, 'partials/shorten_result.html', {
        'form': form,
        'errors': form.errors,
    })


@require_GET
def check_slug(request):
    slug = request.GET.get('slug', '').strip()
    if not slug:
        return render(request, 'partials/slug_check.html', {'status': 'empty'})

    valid, error = validate_slug(slug)
    if not valid:
        return render(request, 'partials/slug_check.html', {
            'status': 'invalid', 'message': error,
        })

    taken = Link.objects.filter(
        Q(short_code=slug) | Q(custom_slug=slug)
    ).exists()

    if taken:
        return render(request, 'partials/slug_check.html', {
            'status': 'taken', 'message': 'This slug is already taken.',
        })

    return render(request, 'partials/slug_check.html', {
        'status': 'available', 'message': 'Available!',
    })


# ---------------------
# Redirect Engine
# ---------------------

def redirect_short_url(request, code):
    try:
        link = Link.objects.get(
            Q(short_code=code) | Q(custom_slug=code),
            is_active=True,
        )
    except Link.DoesNotExist:
        raise Http404

    # Log click in background thread
    ua_string = request.META.get('HTTP_USER_AGENT', '')[:500]
    referrer = request.META.get('HTTP_REFERER', '')[:2048]
    ip = get_client_ip(request)
    geo = get_geo_from_request(request)
    ua_data = parse_user_agent(ua_string)

    def log_click():
        Click.objects.create(
            link=link,
            referrer=referrer,
            user_agent=ua_string,
            country=geo['country'],
            city=geo['city'],
            device_type=ua_data['device_type'],
            browser=ua_data['browser'],
            os=ua_data['os'],
            ip_hash=hash_ip(ip),
        )
        Link.objects.filter(pk=link.pk).update(click_count=F('click_count') + 1)

    t = threading.Thread(target=log_click, daemon=True)
    t.start()

    return redirect(link.original_url)


# ---------------------
# Dashboard
# ---------------------

@login_required
def dashboard(request):
    links = Link.objects.filter(user=request.user)

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        links = links.filter(
            Q(original_url__icontains=q) |
            Q(custom_slug__icontains=q) |
            Q(title__icontains=q) |
            Q(short_code__icontains=q)
        )

    # Sort
    sort = request.GET.get('sort', '-created_at')
    valid_sorts = {'-created_at', 'created_at', '-click_count', 'click_count'}
    if sort not in valid_sorts:
        sort = '-created_at'
    links = links.order_by(sort)

    # Stats
    total_links = Link.objects.filter(user=request.user).count()
    total_clicks = Link.objects.filter(user=request.user).aggregate(
        total=Count('clicks')
    )['total'] or 0
    avg_clicks = round(total_clicks / total_links, 1) if total_links > 0 else 0

    # Pagination
    paginator = Paginator(links, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard/links.html', {
        'page_obj': page_obj,
        'total_links': total_links,
        'total_clicks': total_clicks,
        'avg_clicks': avg_clicks,
        'search_query': q,
        'current_sort': sort,
    })


# ---------------------
# Link Analytics
# ---------------------

@login_required
def link_analytics(request, pk):
    link = get_object_or_404(Link, pk=pk, user=request.user)

    days = int(request.GET.get('days', 30))
    if days not in (7, 30, 90, 365):
        days = 30

    since = timezone.now() - timedelta(days=days)
    clicks = Click.objects.filter(link=link, clicked_at__gte=since)

    # Clicks over time
    clicks_by_date = list(
        clicks.annotate(date=TruncDate('clicked_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Chart data
    chart_labels = [entry['date'].strftime('%Y-%m-%d') for entry in clicks_by_date]
    chart_data = [entry['count'] for entry in clicks_by_date]

    # Top countries
    top_countries = list(
        clicks.exclude(country='')
        .values('country')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Top cities
    top_cities = list(
        clicks.exclude(city='')
        .values('city')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Device breakdown
    device_breakdown = list(
        clicks.exclude(device_type='')
        .values('device_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Browser breakdown
    browser_breakdown = list(
        clicks.exclude(browser='')
        .values('browser')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # OS breakdown
    os_breakdown = list(
        clicks.exclude(os='')
        .values('os')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Top referrers
    top_referrers = list(
        clicks.exclude(referrer='')
        .values('referrer')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Unique visitors
    unique_visitors = clicks.values('ip_hash').distinct().count()

    edit_form = LinkEditForm(initial={
        'original_url': link.original_url,
        'title': link.title,
    })

    return render(request, 'dashboard/link_detail.html', {
        'link': link,
        'total_clicks': clicks.count(),
        'unique_visitors': unique_visitors,
        'days': days,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'top_countries': top_countries,
        'top_cities': top_cities,
        'device_breakdown': device_breakdown,
        'browser_breakdown': browser_breakdown,
        'os_breakdown': os_breakdown,
        'top_referrers': top_referrers,
        'edit_form': edit_form,
    })


# ---------------------
# Link Edit & Delete
# ---------------------

@login_required
@require_POST
def edit_link(request, pk):
    link = get_object_or_404(Link, pk=pk, user=request.user)
    form = LinkEditForm(request.POST)
    if form.is_valid():
        link.original_url = form.cleaned_data['original_url']
        link.title = form.cleaned_data.get('title', '')
        link.save()
    return redirect('link_analytics', pk=pk)


@login_required
@require_POST
def delete_link(request, pk):
    link = get_object_or_404(Link, pk=pk, user=request.user)
    link.is_active = False
    link.save()
    return redirect('dashboard')


# ---------------------
# QR Code Generator
# ---------------------

def qr_generator(request):
    return render(request, 'qr/generator.html')


def generate_qr(request):
    import qrcode
    from qrcode.image.svg import SvgPathImage

    url = request.GET.get('url', '')
    if not url:
        return HttpResponse('URL is required', status=400)

    fg = request.GET.get('fg', '#000000')
    bg = request.GET.get('bg', '#FFFFFF')
    fmt = request.GET.get('format', 'png')

    if fmt == 'svg':
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(image_factory=SvgPathImage)
        response = HttpResponse(content_type='image/svg+xml')
        response['Content-Disposition'] = 'attachment; filename="qr-code.svg"'
        img.save(response)
        return response
    else:
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fg, back_color=bg)
        response = HttpResponse(content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename="qr-code.png"'
        img.save(response)
        return response


# ---------------------
# SEO & Marketing Pages
# ---------------------

def bitly_alternative(request):
    return render(request, 'pages/bitly_alternative.html')


def promise_page(request):
    return render(request, 'pages/promise.html')


def about_page(request):
    return render(request, 'pages/about.html')


def privacy_page(request):
    return render(request, 'pages/privacy.html')


def terms_page(request):
    return render(request, 'pages/terms.html')


def contact_page(request):
    return render(request, 'pages/contact.html')


# ---------------------
# Migration / Import
# ---------------------

@login_required
def migrate_page(request):
    if request.method == 'POST':
        # CSV upload
        csv_file = request.FILES.get('csv_file')
        if csv_file:
            decoded = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            created = 0
            errors = []
            for i, row in enumerate(reader, start=1):
                url = row.get('url', '') or row.get('original_url', '') or row.get('URL', '')
                slug = row.get('slug', '') or row.get('custom_slug', '')
                title = row.get('title', '')
                if not url:
                    errors.append(f"Row {i}: Missing URL")
                    continue
                try:
                    link = Link(
                        original_url=url,
                        user=request.user,
                        title=title,
                    )
                    if slug:
                        valid, err = validate_slug(slug)
                        if valid and not Link.objects.filter(
                            Q(short_code=slug) | Q(custom_slug=slug)
                        ).exists():
                            link.custom_slug = slug
                    link.save()
                    created += 1
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")

            return render(request, 'pages/migrate.html', {
                'created': created,
                'errors': errors,
                'success': True,
            })

    return render(request, 'pages/migrate.html')


# ---------------------
# Utility Endpoints
# ---------------------

def public_stats(request):
    stats = cache.get('site_stats')
    if stats is None:
        from django.utils import timezone
        today = timezone.now().date()
        stats = {
            'totalLinks': Link.objects.count(),
            'linksToday': Link.objects.filter(created_at__date=today).count(),
        }
        cache.set('site_stats', stats, 300)
    else:
        stats = {
            'totalLinks': stats.get('total_links', 0),
            'linksToday': stats.get('links_today', 0),
        }
    return JsonResponse(stats)


def health_check(request):
    try:
        connection.ensure_connection()
        db_status = 'ok'
    except Exception:
        db_status = 'error'

    return JsonResponse({
        'status': 'ok' if db_status == 'ok' else 'error',
        'db': db_status,
        'version': '1.0.0',
    })


# ---------------------
# Custom 404
# ---------------------

def custom_404(request, exception):
    return render(request, '404.html', status=404)


# ---------------------
# Data Export
# ---------------------

@login_required
def export_links_csv(request):
    links = Link.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fattyurl-links.csv"'

    writer = csv.writer(response)
    writer.writerow(['Short URL', 'Original URL', 'Title', 'Clicks', 'Active', 'Created'])
    for link in links:
        writer.writerow([
            link.get_short_url(),
            link.original_url,
            link.title,
            link.click_count,
            link.is_active,
            link.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    return response
