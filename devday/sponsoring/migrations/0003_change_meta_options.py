# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-02-15 13:53
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sponsoring', '0002_add_price_field'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sponsoringpackage',
            options={'ordering': ('-event', '-package_type'), 'verbose_name': 'Sponsoring Package', 'verbose_name_plural': 'Sponsoring Packages'},
        ),
    ]
