# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pushy', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pushnotification',
            name='filter_type',
            field=models.SmallIntegerField(default=0, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pushnotification',
            name='filter_user',
            field=models.IntegerField(default=0, blank=True),
            preserve_default=True,
        ),
    ]
