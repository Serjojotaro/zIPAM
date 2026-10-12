# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Production settings. SECRET_KEY/ALLOWED_HOSTS are mandatory ENV (§38)."""

from .base import env, env_bool, env_list

DEBUG = False

if not env("DJANGO_SECRET_KEY", ""):
    raise RuntimeError("DJANGO_SECRET_KEY is mandatory in production")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env_bool("ZIPAM_SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = env_bool("ZIPAM_CSRF_COOKIE_SECURE", True)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
