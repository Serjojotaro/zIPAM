# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
import factory
from django.contrib.auth.models import Group, User

from apps.ip_addresses.models import IPAddress
from apps.organizations.models import Organization, Tenant
from apps.prefixes.models import Prefix
from apps.sites.models import Region, Site
from apps.vlans.models import VLAN
from apps.vrfs.models import VRF


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall("set_password", "test-pass-123")


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Org {n}")


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Tenant {n}")


class RegionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Region

    name = factory.Sequence(lambda n: f"Region {n}")


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Site

    name = factory.Sequence(lambda n: f"Site {n}")


class VRFFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VRF

    name = factory.Sequence(lambda n: f"vrf{n}")


class VLANFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VLAN

    name = factory.Sequence(lambda n: f"vlan{n}")
    vid = factory.Sequence(lambda n: n % 4094 + 1)


class PrefixFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Prefix

    vrf = factory.SubFactory(VRFFactory)
    prefix = factory.Sequence(lambda n: f"10.{n // 256}.{n % 256}.0/24")


class IPAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IPAddress

    vrf = factory.SubFactory(VRFFactory)
    address = factory.Sequence(lambda n: f"10.{n // 256}.{n % 256}.{n // 65536}")


def make_role_user(role: str) -> User:
    """User assigned to the given role group (group must exist via migration)."""
    user = UserFactory()
    user.groups.add(Group.objects.get(name=role))
    return user
