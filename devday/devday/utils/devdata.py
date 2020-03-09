#!/usr/bin/env python
# -*- coding: utf-8 -*-

import errno
import os
import random
import re
import sys
from datetime import timedelta
from os import makedirs
from os.path import isfile, join
from shutil import copyfile

from cms import api
from cms.models import Page
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.models.static_placeholder import StaticPlaceholder
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import OutputWrapper
from django.core.management.color import no_style
from django.core.paginator import Paginator
from django.utils import timezone

import lorem
import stringcase
from attendee.models import Attendee
from devday.utils.words import Words
from event.models import Event
from speaker.models import Speaker
from talk import COMMITTEE_GROUP
from talk.models import (
    Room,
    Talk,
    TalkFormat,
    TalkMedia,
    TalkSlot,
    TimeSlot,
    Track,
    Vote,
)
from twitterfeed.models import Tweet, TwitterProfileImage

LAST_NAMES = [
    "Schneider",
    "Meier",
    "Schulze",
    "Fischer",
    "Weber",
    "Becker",
    "Lehmann",
    "Koch",
    "Richter",
    "Neumann",
    "Fuchs",
    "Vogel",
    "Keller",
    "Jung",
    "Hahn",
    "Schubert",
    "Winkler",
    "Berger",
    "Lorenz",
    "Albrecht",
]

FIRST_NAMES = [
    "Alexander",
    "Barbara",
    "Christian",
    "Daniela",
    "Erik",
    "Fatima",
    "Georg",
    "Heike",
    "Ingo",
    "Jana",
    "Klaus",
    "Lena",
    "Martin",
    "Natalie",
    "Olaf",
    "Peggy",
    "Quirin",
    "Rosa",
    "Sven",
    "Tanja",
    "Ulrich",
    "Veronika",
    "Werner",
    "Xena",
    "Yannick",
    "Zahra",
]

AVAILABLE_ROOMS = (
    (0, "Hamburg"),
    (1, "Gartensaal"),
    (2, "St. Petersburg"),
    (3, "Rotterdam"),
)

User = get_user_model()


class DevData:
    help = "Fill database with data suitable for development"
    rng = random.Random()
    rng.seed(1)  # we want reproducable pseudo-random numbers here
    speaker_placeholder_file = "icons8-contacts-26.png"
    speaker_placeholder_source_path = join(
        settings.STATICFILES_DIRS[0], "img", speaker_placeholder_file
    )
    speaker_portrait_media_dir = "speakers"
    speaker_portrait_media_path = join(
        speaker_portrait_media_dir, speaker_placeholder_file
    )
    speaker_portrait_dir = join(settings.MEDIA_ROOT, speaker_portrait_media_dir)
    speaker_portrait_path = join(settings.MEDIA_ROOT, speaker_portrait_media_path)
    SPEAKERS_PER_EVENT = 50

    def __init__(self, stdout=None, style=None):
        self.user = None
        self.devnull = open(os.devnull, "w")
        self.stdout = stdout if stdout else OutputWrapper(self.devnull)
        self.style = style if style else no_style()

    def __del__(self):
        if self.devnull:
            self.devnull.close()

    def write_action(self, msg):
        self.stdout.write(msg + "... ", ending="")
        self.stdout.flush()

    def write_ok(self):
        self.stdout.write(" OK", style_func=self.style.SUCCESS)

    def write_error(self):
        self.stdout.write(" FAILED", style_func=self.style.ERROR)

    def write_notice(self, msg):
        self.stdout.write(" OK", style_func=self.style.SUCCESS, ending="")
        self.stdout.write(", " + msg, style_func=self.style.NOTICE)

    def create_objects(self, name, thing, min_count, create, already=None):
        self.write_action("Create {}".format(name))
        count = thing.objects.count()
        if count >= min_count:
            self.write_notice("{} {} already exist".format(count, name))
            if already:
                self.stdout.write(already(), ending="")
            return
        try:
            r = create()
            self.write_ok()
            if r:
                self.stdout.write(r, ending="")
        except Exception:  # pragma: no cover
            self.write_error()
            raise

    def create_admin_user(self):
        self.write_action("Create admin user")
        try:
            self.user = User.objects.get(email=settings.ADMINUSER_EMAIL)
            self.write_notice("{} already present".format(settings.ADMINUSER_EMAIL))
        except ObjectDoesNotExist:
            try:
                self.user = User.objects.create_superuser(
                    settings.ADMINUSER_EMAIL, password="admin"
                )
                self.write_ok()
            except Exception:  # pragma: no cover
                self.write_error()
                raise

    def update_site(self):
        self.write_action("Update site")
        try:
            site = Site.objects.get(pk=1)
            site.domain = "devday.de"
            site.name = "Dev Data"
            site.save()
            self.write_ok()
        except Exception:  # pragma: no cover
            self.write_error()
            raise

    def get_page_title(self, page):
        return page.get_title_obj_attribute("title", "de")

    def add_text_plugin_to_placeholder(self, page, slot, body=None):
        placeholder = page.placeholders.get(slot=slot)
        if not body:
            body = "<h1>{} ({})</h1>\n<p>{}</p>\n".format(
                self.get_page_title(page), stringcase.titlecase(slot), lorem.paragraph()
            )
        api.add_plugin(placeholder, "TextPlugin", "de", body=body)

    def create_pages(self):
        index = api.create_page(
            title="Deutsche Homepage",
            language="de",
            template="devday_index.html",
            parent=None,
            slug="de",
            in_navigation=False,
        )
        index.set_as_homepage()
        self.add_text_plugin_to_placeholder(
            index,
            "eventinfo",
            """<p>Am <strong>05.05.2020 </strong>ist es soweit – der Dev Day findet zum 6ten Mal in der Börse Dresden statt. 
Seid dabei, wenn wir die neusten Innovationen und heißesten Trends der IT-Branche diskutieren.</p>
<p>Für alle die den Dev Day noch nicht kennen – die IT-Konferenz wird von der 
Software Engineering Community der T-Systems Multimedia Solutions veranstaltet und bietet Platz zum 
Netzwerken und Wissensaustausch zu allen IT-Themen. Egal welche Technologie, egal ob 
Trends und Innovationen oder Themen, die euch schon immer beschäftigt haben, wir diskutieren Methodiken, 
Codes und die menschliche Seite in der Softwareentwicklung – auf dem Dev Day ist Platz für alle Themen! 
Dabei sind alle IT-Interessenten herzlich willkommen, egal ob Studierende, Fachexperten oder Quereinsteiger, 
unabhängig von ihrer Erfahrung, ihrem Geschlecht, ihrer ethnischen Herkunft und ihrer Religion!</p>
""",
        )
        self.add_text_plugin_to_placeholder(
            index,
            "cfp_open",
            body="""<h4>Call for Papers</h4><p>Ihr habt ein cooles Thema, 
dass ihr gerne vorstellen wollt? – Dann reicht jetzt eure 
Vorträge für den Dev Day ein und nutzt die Chance eure Vision mit uns zu teilen! 
Wie schon im letzten Jahr bieten wir euch dafür verschiedene Formate an - 
ob 10 Minuten Lightningtalk, 30 oder 60 minütige Session 
oder gar ein Workshop über mehrere Stunden – ihr könnt entscheiden, 
wie ihr die Teilnehmenden von eueren Themen begeistern wollt.</p>
<p>Der Call for Paper ist bis zum 15.01.2020 geöffnet.</p>
<p>Unsicher ob euer Vortrag zu uns passt? – Dann sprecht uns an, 
wir unterstützen gern. Denn wir freuen uns über vielfältige Einreichungen!</p>
""",
        )
        self.add_text_plugin_to_placeholder(
            index,
            "save_the_date",
            body="""<h4>Save the Date</h4>
<p>Der Dev Day 20 findet am <strong>5. Mai 2020</strong> am gewohnten Ort, der
<strong>Börse Dresden</strong> statt.</p>""",
        )
        self.add_text_plugin_to_placeholder(
            index,
            "sign_up",
            body="""<h4>Jetzt anmelden</h4>
<p>Sichert euch jetzt euren kostenfreien Platz auf dem Dev Day!</p>""",
        )
        api.publish_page(index, self.user, "de")

        sponsoring = api.create_page(
            title="Sponsoring",
            language="de",
            published=True,
            template="devday_no_cta.html",
            reverse_id="sponsoring",
            parent=None,
        )
        self.add_text_plugin_to_placeholder(sponsoring, "content")
        api.publish_page(sponsoring, self.user, "de")

        impress = api.create_page(
            title="Impressum",
            language="de",
            published=True,
            template="devday_no_cta.html",
            reverse_id="imprint",
            parent=None,
        )
        self.add_text_plugin_to_placeholder(impress, "content")
        api.publish_page(impress, self.user, "de")

        data_privacy = api.create_page(
            title="Datenschutzhinweise",
            language="de",
            published=True,
            template="devday_no_cta.html",
            reverse_id="data-privacy",
            parent=None,
        )
        self.add_text_plugin_to_placeholder(data_privacy, "content")
        api.publish_page(data_privacy, self.user, "de")

    def create_static_placeholder_text(
        self, name, lang="de", paras=3, title=None, text=None
    ):
        self.write_action('    "{}"'.format(name))

        try:
            try:
                sph = StaticPlaceholder.objects.get(name=name)
                ph = sph.draft
                np = CMSPlugin.objects.filter(placeholder=ph, language=lang).count()
                if np >= 1:  # pragma: no branch
                    self.stdout.write("OK", style_func=self.style.SUCCESS)
                    return
            except ObjectDoesNotExist:
                ph, created = Placeholder.objects.update_or_create(slot=name)
                sph = StaticPlaceholder(name=name, code=name, draft=ph, dirty=True)
                sph.draft = ph
                sph.save()
                sph.publish(None, lang, True)
                # this shouldn't be necessary, but leaving it out will lead
                # to an empty placeholder.
                sph = StaticPlaceholder.objects.get(name=name)
                ph = sph.draft
            if not text:
                text = ""
                for i in range(paras):
                    text += "<p>{}</p>\n".format(lorem.paragraph())
            if not title:
                title = name
            text = "<h1>{}</h1>\n{}".format(title, text)
            p = api.add_plugin(ph, "TextPlugin", lang, body=text)
            p.save()
            sph.publish(None, lang, True)
            self.stdout.write("Created", style_func=self.style.SUCCESS)
        except Exception:  # pragma: no cover
            self.write_error()
            raise

    def update_static_placeholders(self):
        self.stdout.write("Update static placeholders")
        self.create_static_placeholder_text(
            "checkin-instructions",
            title="Check attendee in manually",
            text="A small set of instructions on how to check in an attendee.",
        )
        # find devday -name "*.html" | xargs grep static_placeholder \
        # | sed -nEe 's#^.*static_placeholder "([^"]*)".*$#\1#p' | sort -u
        for placeholder in (
            "create-talk-introtext",
            "checkin-instructions",
            "checkin-result",
            "gdpr_teaser",
            "login-intro",
            "register-attendee-introtext",
            "register-intro",
            "register-intro-anonymous",
            "register-intro-introtext-authenticated",
            "register-success",
            "speaker-register",
            "speaker_registered",
            "sponsoring-intro-text",
            "sponsoring-form-prefix-text",
            "sponsoring-request-thanks",
            "sponsors",
            "submit-session-introtext",
            "talk_submission_closed",
            "talk_submitted",
            "talk-voting-intro-text",
        ):
            self.create_static_placeholder_text(placeholder)

    def create_talk_formats(self):
        formats = [
            {"name": "Vortrag", "duration": 30},
            {"name": "Lightning Talk", "duration": 10},
            {"name": "Workshop", "duration": 180},
        ]
        for i in formats:
            TalkFormat.objects.create(name=i["name"], duration=i["duration"])

    def update_events(self):
        self.write_action("Updating events")
        events = list(Event.objects.order_by("start_time"))
        standard_format = TalkFormat.objects.get(name="Vortrag", duration=60)
        try:
            for e in events[:-1]:
                e.registration_open = False
                e.submission_open = False
                e.save()
                e.talkformat.add(standard_format)
            e = events[-1]
            e.registration_open = True
            e.submission_open = True
            e.save()
            e.talkformat.add(*TalkFormat.objects.all())
            self.write_ok()
        except Exception:  # pragma: no cover
            self.write_error()
            raise

    def get_committee_members(self):
        r = "Program committee users:\n"
        for u in User.objects.filter(groups__name=COMMITTEE_GROUP).order_by("email"):
            r += "    {}\n".format(u.email)
        return r

    def create_users_and_attendees(self, amount=sys.maxsize, events=None):
        if not events:  # pragma: no branch
            events = Event.objects.all()  # pragma: no cover
        length = len(FIRST_NAMES) * len(LAST_NAMES)
        if length > amount:
            length = amount
        self.write_action("{:d} attendees".format(length))
        for first_name in FIRST_NAMES:
            for last_name in LAST_NAMES:
                user = User.objects.create_user(
                    "{}.{}@example.com".format(first_name.lower(), last_name.lower()),
                    password="attendee",
                    contact_permission_date=timezone.now(),
                )
                for e in events:
                    if self.rng.random() < 0.8:
                        Attendee.objects.create(user=user, event=e)
                amount -= 1
                if amount <= 0:
                    return

    def random_twitter_users(self, count):
        for i in range(count):
            first_name = self.rng.choice(FIRST_NAMES)
            last_name = self.rng.choice(LAST_NAMES)
            yield (
                i,
                "{}{}".format(first_name, last_name).lower(),
                "{} {}".format(first_name, last_name),
            )

    def get_name_from_email(self, email):
        m = re.match(r"^([^.]+)\.([^@]+)@.*$", email)
        if m:
            return f"{m.group(1).capitalize()} {m.group(2).capitalize()}"
        else:
            return email

    def create_attendees(self, amount=sys.maxsize, events=None):
        if events is None:  # pragma: no branch
            events = Event.objects.all()
        self.create_users_and_attendees(amount=amount, events=events)
        committee_group = Group.objects.get(name=COMMITTEE_GROUP)
        for user in self.rng.sample(list(User.objects.all()), 7):
            user.groups.add(committee_group)
            user.save()
        return self.get_committee_members()

    def get_speakers(self):
        result = "The first couple of speakers:\n"
        speakers = Speaker.objects.all().order_by("name")
        for speaker in Paginator(speakers, 10).page(1).object_list:
            result += "    {} <{}>\n".format(speaker.name, speaker.user.email)
        return result

    def create_speakers(self, events=None):
        if events is None:
            events = Event.objects.all()
        number_of_speakers = len(events) * self.SPEAKERS_PER_EVENT
        # speakers can come from the whole user population and do not need
        # to be attendees anymore
        users = self.rng.sample(list(User.objects.all())[1:], number_of_speakers)
        self.write_action(
            "creating {} speakers for each of the {} events".format(
                self.SPEAKERS_PER_EVENT, len(events)
            )
        )
        if not isfile(self.speaker_portrait_path):  # pragma: no cover
            try:
                makedirs(self.speaker_portrait_dir)
            except OSError as e:  # pragma: no cover
                if e.errno != errno.EEXIST:
                    raise
            copyfile(self.speaker_placeholder_source_path, self.speaker_portrait_path)
        for user in users:
            if not Speaker.objects.filter(user=user).exists():  # pragma: no branch
                speaker = Speaker(
                    name=self.get_name_from_email(user.email),
                    user=user,
                    video_permission=True,
                    shirt_size=3,
                    short_biography="My short bio",
                )
                # https://stackoverflow.com/a/5256094
                speaker.portrait = speaker.portrait.field.attr_class(
                    speaker, speaker.portrait.field, self.speaker_portrait_media_path
                )
                speaker.save()
        return self.get_speakers()

    def create_talk(self, speaker, formats, event):
        talk = Talk(
            draft_speaker=speaker,
            title=Words.sentence(self.rng).title(),
            abstract=lorem.paragraph(),
            remarks=lorem.paragraph(),
            event=event,
        )
        talk.save()
        talk.talkformat.add(
            *self.rng.sample(formats, self.rng.randint(1, len(formats)))
        )
        return talk

    def create_talks(self, events=Event.objects.all()):
        """
        Create talks. With a probability of 10%, a speaker will submit two
        talks, with a probability of 75% will submit one talk, and with a
        remaining probability of 15% will not submit any talk for the event the
        speaker registered for.
        """
        event_list = list(events)
        for event in events:
            formats = list(TalkFormat.objects.filter(event=event))
            for speaker in Speaker.objects.all():
                if event != self.rng.choice(event_list):
                    continue
                p = self.rng.random()
                if p < 0.85:
                    self.create_talk(speaker, formats, event)
                if p < 0.10:
                    self.create_talk(speaker, formats, event)

    def create_talk_media(self, talks=Talk.objects.all()):
        for talk in list(talks):
            talk.media = TalkMedia()
            talk.media.talk = talk

            if self.rng.randint(0, 2) > 0:
                talk.media.youtube = "E5VN-MI1mZA"
            if self.rng.randint(0, 2) > 0:
                talk.media.slideshare = "zEvpGJkZqrLIGa"
            if self.rng.randint(0, 2) > 0:
                talk.media.codelink = "https://github.com/devdaydresden/devday_website"
            talk.media.save()

    def vote_for_talk(self, events=None):
        if events is None:  # pragma: no branch
            events = (Event.objects.current_event(),)
        committee = User.objects.filter(groups__name=COMMITTEE_GROUP)
        for event in events:
            for talk in Talk.objects.filter(event=event):
                for user in committee:
                    p = self.rng.randint(0, 6)
                    if p > 0:
                        Vote.objects.create(voter=user, talk=talk, score=p)
        return "Cast {} votes".format(Vote.objects.count())

    def create_tracks(self, events=None):
        if events is None:
            events = Event.objects.all_but_current()
        tracks = {
            "devdata.17": [
                "The Human Side",
                "Architektur",
                "Let Data Rule",
                "DevOps",
                "Keynote",
            ],
            "devdata.18": [
                "Methodik",
                "Frontend",
                "Coding",
                "Keynote",
                "The Human Side",
                "Exkursion",
            ],
        }
        for event in events:
            for track_name in tracks.setdefault(
                event.title, ["Keynote", "Coding", "Philosophy"]
            ):
                track = Track(name=track_name, event=event)
                track.save()

    def create_rooms(self, events=None):
        if events is None:
            events = Event.objects.all_but_current()
        for event in events:
            [
                Room.objects.create(name=name, event=event, priority=priority)
                for priority, name in AVAILABLE_ROOMS
            ]

    def create_time_slots(self, events=None):
        if events is None:
            events = Event.objects.all()
        time_slots = (
            (10, 30, 12, 0, "Exkursion"),
            (12, 0, 13, 0, "Registrierung"),
            (13, 0, 13, 15, "Begrüßung durch die SECO"),
            (13, 15, 14, 15, "Keynote"),
            (14, 15, 14, 30, "Kurze Pause"),
            (14, 30, 15, 15, ""),
            (15, 15, 15, 45, "Kaffeepause"),
            (15, 45, 16, 30, ""),
            (16, 30, 16, 45, "Kurze Pause"),
            (16, 45, 17, 30, ""),
            (17, 30, 17, 45, "Kurze Pause"),
            (17, 45, 18, 45, "Keynote"),
            (18, 45, 20, 30, "Get Together"),
        )
        for start_hour, start_minute, end_hour, end_minute, text in time_slots:
            name = "{:02d}:{:02d} \u2014 {:02d}:{:02d}".format(
                start_hour, start_minute, end_hour, end_minute
            )
            for event in events:
                start = event.start_time.replace(hour=start_hour, minute=end_hour)
                end = event.end_time.replace(hour=end_hour, minute=end_minute)
                TimeSlot.objects.create(
                    name=name,
                    event=event,
                    start_time=start,
                    end_time=end,
                    text_body=text,
                )

    def create_talk_slots(self, events=None):
        if events is None:
            events = Event.objects.all_but_current()
        details = ""
        for event in events:
            keynote_room = Room.objects.get(name="Hamburg", event=event)
            tracks = Track.objects.filter(event=event).exclude(name="Keynote")
            rooms = Room.objects.filter(event=event)
            keynote_track = Track.objects.get(event=event, name="Keynote")
            keynote_slots = TimeSlot.objects.filter(event=event, text_body="Keynote")
            session_slots = TimeSlot.objects.filter(event=event, text_body="")
            number_of_talks = len(keynote_slots) + len(session_slots) * len(rooms)
            details += (
                "    {}: {} talks for {} keynotes, and {} sessions in {} rooms" "\n"
            ).format(
                event.title,
                number_of_talks,
                len(keynote_slots),
                len(session_slots),
                len(rooms),
            )
            talks = self.rng.sample(
                list(Talk.objects.filter(event=event)), number_of_talks
            )
            for time_slot in keynote_slots:
                talk = talks.pop()
                TalkSlot.objects.create(time=time_slot, room=keynote_room, talk=talk)
                talk.publish(track=keynote_track)
            for time_slot in session_slots:
                for room in rooms:
                    talk = talks.pop()
                    TalkSlot.objects.create(time=time_slot, room=room, talk=talk)
                    talk.publish(self.rng.choice(tracks))
        return details

    def create_twitter_profiles(self):
        profile_image = TwitterProfileImage.objects.create(
            user_profile_image_url="http://localhost/twitter_profile.png"
        )
        # https://stackoverflow.com/a/5256094
        profile_image.image_data = profile_image.image_data.field.attr_class(
            profile_image, profile_image.image_data, self.speaker_portrait_media_path
        )
        profile_image.save()

    def create_tweets(self, count=7):
        profile_image = TwitterProfileImage.objects.get(
            user_profile_image_url="http://localhost/twitter_profile.png"
        )
        dt = timezone.now() - timedelta(days=-count)
        for twitter_id, handle, username in self.random_twitter_users(count):
            text = lorem.sentence()
            Tweet.objects.create(
                twitter_id=twitter_id,
                user_profile_image=profile_image,
                user_name=username,
                user_screen_name=handle,
                text=text,
                plain_text=text,
                entities="{}",
                created_at=dt,
                show_on_site=True,
            )
            dt += timedelta(
                days=1, hours=self.rng.randrange(3), minutes=self.rng.randrange(30)
            )

    def create_devdata(self):
        self.create_admin_user()
        self.update_site()
        self.update_static_placeholders()
        self.create_objects("talk formats", TalkFormat, 3, self.create_talk_formats)
        self.update_events()
        self.create_objects("pages", Page, 3, self.create_pages)
        self.create_objects(
            "users", User, 3, self.create_attendees, self.get_committee_members
        )
        # TODO: create some speakers from the user population
        self.create_objects(
            "speakers", Speaker, 1, self.create_speakers, self.get_speakers
        )
        # TODO: create published speakers for published talks
        self.create_objects("talks", Talk, 1, self.create_talks)
        self.create_objects("talk media", TalkMedia, 1, self.create_talk_media)
        # TODO: vote on unpublished talks only
        self.create_objects("votes", Vote, 1, self.vote_for_talk)
        self.create_objects("tracks", Track, 1, self.create_tracks)
        self.create_objects("rooms", Room, 1, self.create_rooms)
        self.create_objects("time slots", TimeSlot, 1, self.create_time_slots)
        self.create_objects("talk slots", TalkSlot, 1, self.create_talk_slots)
        self.create_objects(
            "twitter profiles", TwitterProfileImage, 1, self.create_twitter_profiles
        )
        self.create_objects("tweets", Tweet, 1, self.create_tweets)
