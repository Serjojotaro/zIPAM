# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from typing import Any

from django.db import migrations

GLOBAL_VRF_NAME = "global"


def bootstrap_global_vrf(apps: Any, schema_editor: Any) -> None:
    VRF = apps.get_model("vrfs", "VRF")
    VRF.objects.get_or_create(name=GLOBAL_VRF_NAME)


def remove_global_vrf(apps: Any, schema_editor: Any) -> None:
    VRF = apps.get_model("vrfs", "VRF")
    VRF.objects.filter(name=GLOBAL_VRF_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("vrfs", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(bootstrap_global_vrf, remove_global_vrf),
    ]
