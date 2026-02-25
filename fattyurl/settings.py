from pathlib import Path
import environ

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    DATABASE_URL=(str, 'sqlite:///db.sqlite3'),
    ADMINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    EMAIL_HOST=(str, ''),
    EMAIL_PORT=(int, 25),
    EMAIL_USE_TLS=(bool, False),
    EMAIL_USE_SSL=(bool, False),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_HOST_PASSWORD=(str, ''),
    EMAIL_FROM=(str, 'noreply@localhost'),
    USE_X_FORWARDED_HOST=(bool, False),
    SECURE_PROXY_SSL_HEADER_NAME=(str, 'HTTP_X_FORWARDED_PROTO'),
    SECURE_PROXY_SSL_HEADER_VALUE=(str, 'https'),
)

BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

if not DEBUG:
    CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_REDIRECT_EXEMPT = []
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    CSRF_COOKIE_HTTPONLY = True

ADMINS = []
for _admin in env.list('ADMINS', default=[]):
    if not _admin.strip():
        continue
    if ':' in _admin:
        _name, _email = _admin.split(':', 1)
        if _name.strip() and _email.strip():
            ADMINS.append((_name.strip(), _email.strip()))
    else:
        ADMINS.append(('', _admin.strip()))
MANAGERS = ADMINS

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    # Third party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'rest_framework',
    # Local
    'core',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'core.middleware.RateLimitMiddleware',
]

if DEBUG:
    INSTALLED_APPS = INSTALLED_APPS + ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

ROOT_URLCONF = 'fattyurl.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_stats',
                'core.context_processors.social_provider_status',
            ],
        },
    },
]

WSGI_APPLICATION = 'fattyurl.wsgi.application'

DATABASES = {
    'default': env.db(default='sqlite:///db.sqlite3')
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Sites
SITE_ID = 1

# django-allauth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_ON_SIGNUP = True
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = True

# OAuth providers
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': env('GOOGLE_CLIENT_ID', default=''),
            'secret': env('GOOGLE_CLIENT_SECRET', default=''),
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
    'github': {
        'APP': {
            'client_id': env('GITHUB_CLIENT_ID', default=''),
            'secret': env('GITHUB_CLIENT_SECRET', default=''),
        },
        'SCOPE': ['user:email'],
    },
}

SOCIALACCOUNT_ADAPTER = 'core.adapters.ForceAutoSignupSocialAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'api.authentication.APIKeyAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Cache (in-memory for dev, switch to Redis in production)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Email (console for dev)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST', default='localhost')
    EMAIL_PORT = env('EMAIL_PORT', default=25)
    EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=False)
    EMAIL_USE_SSL = env('EMAIL_USE_SSL', default=False)
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
    DEFAULT_FROM_EMAIL = env('EMAIL_FROM', default='noreply@localhost')
    SERVER_EMAIL = env('EMAIL_FROM', default=DEFAULT_FROM_EMAIL)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
            'filters': ['require_debug_false'],
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
