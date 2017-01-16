# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-11 11:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('talk', '0007_auto_20170106_1249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='talkcomment',
            name='comment',
            field=models.TextField(verbose_name='Comment'),
        ),
        migrations.AlterField(
            model_name='talkcomment',
            name='is_visible',
            field=models.BooleanField(default=False, help_text='Indicates whether the comment is visible to the speaker.', verbose_name='Visible for Speaker'),
        ),
    ]