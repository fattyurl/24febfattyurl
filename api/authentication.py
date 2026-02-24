import hashlib
import secrets

from rest_framework import authentication, exceptions

from core.models import UserProfile


class APIKeyAuthentication(authentication.BaseAuthentication):
    """Bearer token authentication using API keys."""

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        api_key = auth_header[7:].strip()
        if not api_key:
            return None

        key_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
        try:
            profile = UserProfile.objects.select_related('user').get(api_key_hash=key_hash)
            return (profile.user, None)
        except UserProfile.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key.')

    @staticmethod
    def generate_api_key():
        """Generate a new API key and return (raw_key, key_hash, prefix)."""
        raw_key = f"fatty_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
        prefix = raw_key[:12]
        return raw_key, key_hash, prefix
