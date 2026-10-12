# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Settings for the pytest suite (runs against a real PostgreSQL — no SQLite
substitutes, so PG-specific behavior (GiST, inet/cidr) is exercised)."""

from .base import *  # noqa: F403
from .base import env

SECRET_KEY = "test-only-secret-key"
DEBUG = False
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "zipam"),
        "USER": env("POSTGRES_USER", "zipam"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
