"""
Django settings for expense_tracker project.
"""

from datetime import timedelta
from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-dev-only-change-me-in-production",
)

DEBUG = os.environ.get("DEBUG", "True").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if h.strip()
]
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

# Render sets RENDER_EXTERNAL_HOSTNAME
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    # Local
    "accounts",
    "tracker",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "expense_tracker.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "expense_tracker.wsgi.application"


def _normalize_database_url(url: str) -> str:
    """
    Fix common malformed Render DATABASE_URL paste mistakes:
    1) Missing '@' before host:
         postgresql://user:passworddpg-xxxxx/dbname
    2) Password placed where the port should be:
         postgresql://user@dpg-xxxxx:PASSWORD/dbname
       → postgresql://user:PASSWORD@dpg-xxxxx/dbname
    """
    import re
    from urllib.parse import quote, urlparse, urlunparse

    if not url or "://" not in url:
        return url

    # Case 2: user@host:non-numeric-port/db  (password stuck in port slot)
    swapped = re.match(
        r"^(postgres(?:ql)?://)([^:/@]+)@([a-z0-9.-]+):([^/]+)(/.*)?$",
        url,
        re.IGNORECASE,
    )
    if swapped:
        scheme, user, host, password, path = swapped.groups()
        if not password.isdigit():
            url = f"{scheme}{user}:{password}@{host}{path or ''}"

    scheme, rest = url.split("://", 1)
    if "@" not in rest:
        # Case 1: missing @ before dpg- host
        match = re.match(
            r"^([^:]+):(.+?)(dpg-[a-z0-9.-]+)(/.*)?$",
            rest,
            re.IGNORECASE,
        )
        if match:
            user, password, host, path = match.groups()
            rest = f"{user}:{password}@{host}{path or ''}"
            url = f"{scheme}://{rest}"

    # Percent-encode password if it contains reserved characters
    try:
        parsed = urlparse(url)
        if parsed.password and any(c in parsed.password for c in "@:#/?%"):
            user = quote(parsed.username or "", safe="")
            password = quote(parsed.password, safe="")
            host = parsed.hostname or ""
            port = f":{parsed.port}" if parsed.port else ""
            netloc = f"{user}:{password}@{host}{port}"
            url = urlunparse(
                (
                    parsed.scheme,
                    netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
    except ValueError:
        # Last resort: strip a non-numeric :port segment
        url = re.sub(
            r"@(dpg-[a-z0-9.-]+):[^/]+/",
            r"@\1/",
            url,
            flags=re.IGNORECASE,
        )
    return url


def _database_from_url(url: str) -> dict:
    """Parse DATABASE_URL safely even when paste-mangled."""
    import re
    from urllib.parse import unquote

    url = _normalize_database_url(url.strip().strip('"').strip("'"))

    try:
        return dj_database_url.parse(
            url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    except ValueError:
        pass

    # user:password@host[/db] (ignore bogus port)
    match = re.search(
        r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+)(?::[^/]*)?(?:/([^?\s]+))?",
        url,
        re.IGNORECASE,
    )
    if match:
        user, password, host, name = match.groups()
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(name or ""),
            "USER": unquote(user),
            "PASSWORD": unquote(password),
            "HOST": host,
            "PORT": "5432",
            "CONN_MAX_AGE": 600,
            "CONN_HEALTH_CHECKS": True,
        }

    # user@host:password/db  (password in port slot)
    match = re.search(
        r"postgres(?:ql)?://([^@/]+)@([^:]+):([^/]+)/([^?\s]+)",
        url,
        re.IGNORECASE,
    )
    if match:
        user, host, password, name = match.groups()
        if not password.isdigit():
            return {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": unquote(name),
                "USER": unquote(user),
                "PASSWORD": unquote(password),
                "HOST": host,
                "PORT": "5432",
                "CONN_MAX_AGE": 600,
                "CONN_HEALTH_CHECKS": True,
            }

    raise ValueError(
        "DATABASE_URL is malformed. Re-copy the Internal Database URL from Render "
        "Postgres (must look like postgresql://USER:PASSWORD@HOST/DBNAME), "
        "or set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT."
    )


def _build_databases():
    """Prefer discrete DB_* vars when set; otherwise DATABASE_URL / SQLite."""
    db_host = os.environ.get("DB_HOST") or os.environ.get("PGHOST")
    if db_host:
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.environ.get("DB_NAME")
                or os.environ.get("PGDATABASE", ""),
                "USER": os.environ.get("DB_USER") or os.environ.get("PGUSER", ""),
                "PASSWORD": os.environ.get("DB_PASSWORD")
                or os.environ.get("PGPASSWORD", ""),
                "HOST": db_host,
                "PORT": os.environ.get("DB_PORT")
                or os.environ.get("PGPORT", "5432"),
                "CONN_MAX_AGE": 600,
                "CONN_HEALTH_CHECKS": True,
            }
        }

    raw = os.environ.get("DATABASE_URL")
    if raw:
        return {"default": _database_from_url(raw)}

    return {
        "default": dj_database_url.parse(
            f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600,
            conn_health_checks=True,
        )
    }


DATABASES = _build_databases()

# Avoid hard-failing health checks before TLS is ready on some free-tier boots
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Default False so first deploy/health checks are less brittle; set True in env if desired
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False").lower() in (
        "1",
        "true",
        "yes",
    )
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS — public frontend may be on any origin during development
_cors_all = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "True").lower() in (
    "1",
    "true",
    "yes",
)
if _cors_all:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = False
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOWED_ORIGINS = [
        o.strip()
        for o in os.environ.get(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173",
        ).split(",")
        if o.strip()
    ]

# DRF — Expense Tracker APIs are public (no JWT required)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Expense Tracker API",
    "DESCRIPTION": "Backend API for expense tracking — auth, categories, transactions, budgets, reports.",
    "VERSION": "1.0.0",
}
