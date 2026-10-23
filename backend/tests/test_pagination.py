# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
"""Client-tunable page size (address-grid support, §23)."""

import pytest
from django.test import Client

from tests.factories import PrefixFactory, VRFFactory, make_role_user

pytestmark = pytest.mark.django_db

PREFIX_LIST = "/api/v1/prefixes/"


@pytest.fixture
def three_prefixes() -> None:
    vrf = VRFFactory()
    for i in range(3):
        PrefixFactory(vrf=vrf, prefix=f"10.77.{i}.0/24")


def test_page_size_param_limits_page(client: Client, three_prefixes: None) -> None:
    client.force_login(make_role_user("viewer"))
    response = client.get(PREFIX_LIST, {"page_size": 2})
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2 and body["count"] == 3


def test_page_size_capped_at_max(client: Client, three_prefixes: None) -> None:
    client.force_login(make_role_user("viewer"))
    response = client.get(PREFIX_LIST, {"page_size": 999999})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 3
