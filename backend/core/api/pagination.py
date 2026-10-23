# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Paginated responses with a client-tunable page size.

The UI address grid (§23) needs a whole small prefix (up to /22, 1024
addresses) in one request; larger lists stay server-paginated (§14)."""

from rest_framework.pagination import PageNumberPagination

MAX_PAGE_SIZE = 1024


class ZipamPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = MAX_PAGE_SIZE
