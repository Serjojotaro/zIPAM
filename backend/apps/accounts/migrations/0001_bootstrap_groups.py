# Copyright 2026 The zIPAM Project Authors
# SPDX-License-Identifier: Apache-2.0
from django.db import migrations


def forwards(apps, schema_editor) -> None:  # type: ignore[no-untyped-def]
    Group = apps.get_model("auth", "Group")
    for name in ("viewer", "operator", "admin"):
        Group.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    initial = True

    dependencies = [("auth", "0012_alter_user_first_name_max_length")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
