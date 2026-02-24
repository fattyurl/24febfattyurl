import csv

from django.db.models import Q
from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Link, Click
from core.utils import validate_url, validate_slug
from .serializers import (
    LinkSerializer, LinkCreateSerializer, LinkUpdateSerializer,
    ClickSerializer, BulkCreateSerializer,
)


@api_view(['POST'])
def shorten(request):
    """Create a short link."""
    serializer = LinkCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    url = serializer.validated_data['url']
    valid, error = validate_url(url)
    if not valid:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

    custom_slug = serializer.validated_data.get('custom_slug', '').strip()
    if custom_slug:
        valid, error = validate_slug(custom_slug)
        if not valid:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        if Link.objects.filter(Q(short_code=custom_slug) | Q(custom_slug=custom_slug)).exists():
            return Response({'error': 'This slug is already taken.'}, status=status.HTTP_409_CONFLICT)

    link = Link(
        original_url=url,
        title=serializer.validated_data.get('title', ''),
        user=request.user if request.user.is_authenticated else None,
    )
    if custom_slug:
        link.custom_slug = custom_slug
    link.save()

    return Response(
        LinkSerializer(link, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_links(request):
    """List user's links."""
    links = Link.objects.filter(user=request.user)

    q = request.query_params.get('q', '').strip()
    if q:
        links = links.filter(
            Q(original_url__icontains=q) |
            Q(custom_slug__icontains=q) |
            Q(title__icontains=q) |
            Q(short_code__icontains=q)
        )

    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(links, request)
    serializer = LinkSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def link_detail(request, pk):
    """Get, update, or delete a single link."""
    try:
        link = Link.objects.get(pk=pk, user=request.user)
    except Link.DoesNotExist:
        return Response({'error': 'Link not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(LinkSerializer(link, context={'request': request}).data)

    elif request.method == 'PATCH':
        serializer = LinkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if 'original_url' in serializer.validated_data:
            url = serializer.validated_data['original_url']
            valid, error = validate_url(url)
            if not valid:
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            link.original_url = url

        if 'title' in serializer.validated_data:
            link.title = serializer.validated_data['title']

        if 'is_active' in serializer.validated_data:
            link.is_active = serializer.validated_data['is_active']

        if 'custom_slug' in serializer.validated_data:
            slug = serializer.validated_data['custom_slug'].strip()
            if slug:
                valid, error = validate_slug(slug)
                if not valid:
                    return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
                if Link.objects.filter(
                    Q(short_code=slug) | Q(custom_slug=slug)
                ).exclude(pk=link.pk).exists():
                    return Response({'error': 'Slug already taken.'}, status=status.HTTP_409_CONFLICT)
                link.custom_slug = slug
            else:
                link.custom_slug = None

        link.save()
        return Response(LinkSerializer(link, context={'request': request}).data)

    elif request.method == 'DELETE':
        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def link_clicks(request, pk):
    """Paginated click log for a link."""
    try:
        link = Link.objects.get(pk=pk, user=request.user)
    except Link.DoesNotExist:
        return Response({'error': 'Link not found.'}, status=status.HTTP_404_NOT_FOUND)

    clicks = Click.objects.filter(link=link)

    from_date = request.query_params.get('from')
    to_date = request.query_params.get('to')
    if from_date:
        clicks = clicks.filter(clicked_at__gte=from_date)
    if to_date:
        clicks = clicks.filter(clicked_at__lte=to_date)

    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(clicks, request)
    serializer = ClickSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_create(request):
    """Bulk create links (max 100)."""
    serializer = BulkCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    results = []
    for item in serializer.validated_data['links']:
        url = item['url']
        valid, error = validate_url(url)
        if not valid:
            results.append({'url': url, 'error': error})
            continue

        link = Link(
            original_url=url,
            title=item.get('title', ''),
            user=request.user,
        )

        custom_slug = item.get('custom_slug', '').strip()
        if custom_slug:
            slug_valid, slug_error = validate_slug(custom_slug)
            if not slug_valid:
                results.append({'url': url, 'error': slug_error})
                continue
            if Link.objects.filter(Q(short_code=custom_slug) | Q(custom_slug=custom_slug)).exists():
                results.append({'url': url, 'error': 'Slug already taken.'})
                continue
            link.custom_slug = custom_slug

        link.save()
        results.append(LinkSerializer(link, context={'request': request}).data)

    return Response({'results': results}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv(request):
    """Export user's links as CSV."""
    links = Link.objects.filter(user=request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fattyurl-links.csv"'

    writer = csv.writer(response)
    writer.writerow(['Short URL', 'Original URL', 'Title', 'Clicks', 'Active', 'Created'])
    for link in links:
        writer.writerow([
            link.get_short_url(request=request),
            link.original_url,
            link.title,
            link.click_count,
            link.is_active,
            link.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    return response
