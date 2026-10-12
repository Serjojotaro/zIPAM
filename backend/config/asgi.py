# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()
