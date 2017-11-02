import json
from datetime import datetime, timedelta
from email.utils import parsedate_tz

import pytz
import requests
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import BaseCommand
from django.core.management import CommandError
from django.db.transaction import atomic

from attendee.models import DevDayUser

class Command(BaseCommand):
    help = 'Print out a list of all users that have agreed to be contacted by the team'

    def handle(self, *args, **options):
        users = DevDayUser.objects.all().filter(contact_permission_date__isnull=False).order_by('email')
        for user in users:
            print "{}".format(user.email)
