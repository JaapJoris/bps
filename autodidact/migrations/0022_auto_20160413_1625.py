# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-13 16:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autodidact', '0021_auto_20160413_1601'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clarification',
            options={'ordering': ['number']},
        ),
        migrations.AlterModelOptions(
            name='presentation',
            options={'ordering': ['file']},
        ),
        migrations.RenameField(
            model_name='clarification',
            old_name='order',
            new_name='number',
        ),
        migrations.RemoveField(
            model_name='presentation',
            name='order',
        ),
    ]
