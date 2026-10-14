# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from apps.vrfs.models import GLOBAL_VRF_NAME, VRF


def get_or_create_global_vrf() -> VRF:
    """Default routing table. Prefixes/addresses attach to a VRF explicitly;
    this is the implicit 'global' table (§10)."""
    vrf, _ = VRF.objects.get_or_create(name=GLOBAL_VRF_NAME)
    return vrf
