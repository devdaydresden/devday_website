#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.core.management import BaseCommand
from devday.utils.devdata import DevData


class Command(BaseCommand):
    help = 'Fill database with data suitable for development'

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout, stderr, no_color)
        self.user = None

    def handle(self, *args, **options):
        devdata = DevData(stdout=self.stdout, style=self.style)
        devdata.create_devdata()
