# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pushy', '0002_auto_20141011_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='pushnotification',
            name='date_finished',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='pushnotification',
            name='date_started',
            field=models.DateTimeField(null=True),
        ),
    ]
