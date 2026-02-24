import time
from django.core.cache import cache
from django.http import JsonResponse


class RateLimitMiddleware:
    """Simple rate limiting middleware using Django cache."""

    RATE_LIMITS = {
        '/shorten/': {'anonymous': 100, 'authenticated': 1000, 'window': 3600},
        '/check-slug/': {'anonymous': 60, 'authenticated': 60, 'window': 60},
        '/qr/generate/': {'anonymous': 120, 'authenticated': 120, 'window': 3600},
        '/api/stats': {'anonymous': 30, 'authenticated': 30, 'window': 60},
        '/api/v1/': {'anonymous': 100, 'authenticated': 1000, 'window': 3600},
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        limit_config = None
        for prefix, config in self.RATE_LIMITS.items():
            if path.startswith(prefix):
                limit_config = config
                break

        if limit_config:
            if request.user.is_authenticated:
                key = f"ratelimit:{request.user.id}:{path}"
                max_requests = limit_config['authenticated']
            else:
                ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
                key = f"ratelimit:{ip}:{path}"
                max_requests = limit_config['anonymous']

            window = limit_config['window']
            current = cache.get(key, 0)

            if current >= max_requests:
                return JsonResponse(
                    {'error': 'Rate limit exceeded. Please try again later.'},
                    status=429,
                )

            cache.set(key, current + 1, window)

        return self.get_response(request)
