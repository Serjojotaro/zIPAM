# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("csrf", views.auth_csrf, name="csrf"),
    path("login", views.auth_login, name="login"),
    path("logout", views.auth_logout, name="logout"),
    path("me", views.auth_me, name="me"),
]
