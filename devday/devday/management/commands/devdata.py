import json
from datetime import datetime, timedelta
from email.utils import parsedate_tz

import pytz
import random
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import BaseCommand
from django.core.management import CommandError
from django.db.transaction import atomic
from django.utils import timezone

from cms import api, constants
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page

from attendee.models import Attendee, DevDayUser
from event.models import Event


class Command(BaseCommand):
    help = 'Fill database with data suitable for development'

    def handleCreateUser(self):
        User = get_user_model()

        try:
            user = User.objects.get(email=settings.ADMINUSER_EMAIL)
            print "Create admin user: {} already present".format(settings.ADMINUSER_EMAIL)
        except ObjectDoesNotExist:
            print "Create admin user"
            user = User.objects.create_user(settings.ADMINUSER_EMAIL, password='admin')
            user.is_superuser=True
            user.is_staff=True
            user.save()

    def handleUpdateSite(self):
        print "Update site"
        site = Site.objects.get(pk=1)
        site.domain = 'devday.de'
        site.name = 'Dev Data'
        site.save()

    def handleCreatePages(self):
        npage = len(Page.objects.all())
        if npage > 0:
            print "Create pages: {} page objects already exist, skipping".format(npage)
            return
        print "Creating pages"
        homepage = api.create_page(title="Dev Data 2019", language='de',
            template='devday_index.html', parent=None)
        api.create_page(title="Deutsche Homepage", language="de",
            template=TEMPLATE_INHERITANCE_MAGIC, redirect="/",
            slug="de",
            in_navigation=False, parent=None)
        api.create_page(title="Sessions", language="de",
            template=TEMPLATE_INHERITANCE_MAGIC, redirect="/devdata19/talk",
            in_navigation=True, parent=None)
        archive = api.create_page(title="Archiv", language="de",
            template=TEMPLATE_INHERITANCE_MAGIC,
            in_navigation=True, parent=None)
        api.create_page(title="Dev Data 2017", language="de",
            template=TEMPLATE_INHERITANCE_MAGIC, redirect="/devdata17/talk",
            in_navigation=True, parent=archive)
        api.create_page(title="Dev Data 2018", language="de",
            template=TEMPLATE_INHERITANCE_MAGIC, redirect="/devdata18/talk",
            in_navigation=True, parent=archive)
        api.create_page(title="Sponsoring", language="de",
            template=TEMPLATE_INHERITANCE_MAGIC,
            reverse_id="sponsoring", parent=None)

    def handleCreateEvents(self):
        # The event with ID 1 has already been created by a migration
        nevent = len(Event.objects.all())
        if nevent > 1:
            print "Creating events: {} events already exist, skipping".format(nevent)
            return
        print "Creating events"
        event = Event(id=2, title='devdata.18', slug='devdata18',
                      description='Dev Data.18 am 24.4. in Dresden', location='Dresden',
                      full_day=False, start_time=timezone.make_aware(datetime(2018, 4, 24, 13, 0)),
                      end_time=timezone.make_aware(datetime(2018, 4, 24, 20, 0)))
        event.save()
        event = Event(id=3, title='devdata.19', slug='devdata19',
                      description='Dev Data.19 am 21.5. in Dresden', location='Dresden',
                      full_day=False, start_time=timezone.make_aware(datetime(2019, 5, 21, 13, 0)),
                      end_time=timezone.make_aware(datetime(2019, 5, 21, 20, 0)))
        event.save()

    def handleCreateAttendees(self):
        User = get_user_model()
        nuser = len(User.objects.all())
        if nuser > 3:
            print "Create attendees: {} attendees already exist, skipping".format(nuser)
            return
        print "Creating attendees"
        events = Event.objects.all()
        rng = random.SystemRandom()
        first = ["Alexander", "Barbara", "Christian", "Daniela", "Erik",
            "Fatima", "Georg", "Heike", "Ingo", "Jana", "Klaus", "Lena",
            "Martin", "Natalie", "Olaf", "Peggy", "Quirin", "Rosa",
            "Sven", "Tanja", "Ulrich", "Veronika", "Werner", "Xena", "Yannick",
            "Zahra"]
        last = ["Schneider", "Meier", "Schulze", "Fischer", "Weber",
            "Becker", "Lehmann", "Koch", "Richter", "Neumann"]
        for f in first:
            for l in last:
                user = User.objects.create_user("{}.{}@example.com".format(f.lower(), l.lower()),
                    password='attendee', first_name=f, last_name=l)
                user.save()
                for e in events:
                    if rng.random() < 0.8:
                        a = Attendee(user=user, event=e)
                        a.save()

    def handle(self, *args, **options):
        self.handleCreateUser()
        self.handleUpdateSite()
        self.handleCreatePages()
        self.handleCreateEvents()
        self.handleCreateAttendees()
