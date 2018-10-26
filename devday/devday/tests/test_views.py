from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.test import TestCase
from django.utils import timezone

from attendee.models import Attendee
from attendee.tests import attendee_testutils
from devday.views import DevDayEmailMessage, DevDayEmailRecipients
from devday.utils.devdata import DevData
from event.models import Event
from speaker.models import PublishedSpeaker, Speaker
from speaker.tests import speaker_testutils
from talk.models import Talk


User = get_user_model()


class TestExceptionTestView(TestCase):
    def test_raises_500_error(self):
        self.assertRaises(
            Exception, self.client.get, u'/synthetic_server_error/')


class BaseTemplateTest(TestCase):
    """
    Tests for correct parsing of the base template for different types of
    users.
    """

    def setUp(self):
        dev_data = DevData()
        dev_data.create_admin_user()
        dev_data.create_pages()
        self.event = Event.objects.current_event()
        self.url = "/"

    def test_parse_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")

    def test_parse_user(self):
        user, password = attendee_testutils.create_test_user()
        self.client.login(username=user.email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")

    def test_parse_attendee(self):
        user, password = attendee_testutils.create_test_user()
        Attendee.objects.create(user=user, event=self.event)
        self.client.login(username=user.email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")

    def test_parse_speaker(self):
        _, user, password = speaker_testutils.create_test_speaker()
        self.client.login(username=user.email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")

    def test_parse_committee_member(self):
        user, password = attendee_testutils.create_test_user()
        group = Group.objects.get(name='talk_committee')
        user.groups.add(group)
        user.save()
        self.client.login(username=user.email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")

    def test_parse_staff(self):
        user, password = attendee_testutils.create_test_user()
        user.is_staff = True
        user.save()
        self.client.login(username=user.email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")

    def test_parse_superuser(self):
        user, password = attendee_testutils.create_test_user()
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.client.login(username=user.email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")


class TestLoginTemplate(TestCase):
    def setUp(self):
        self.url = "/accounts/login/"

    def test_parse_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "django_registration/login.html")

    def test_parse_anonymous_attendee_registration_open(self):
        event = Event.objects.current_event()
        event.registration_open = True
        event.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "django_registration/login.html")


class TestLogin(TestCase):
    def setUp(self):
        self.url = "/accounts/login/"

    def test_post_performs_login(self):
        user, password = attendee_testutils.create_test_user()
        response = self.client.post(
            self.url, data={'username': user.email, 'password': password})
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertEqual(response.context['request'].user, user)


class DevDayEmailRecipientsTest(TestCase):
    def setUp(self):
        self.recipients = DevDayEmailRecipients()
        attendee_testutils.create_test_user('nocontact@example.com')
        user, _ = attendee_testutils.create_test_user('contact@example.com')
        user.contact_permission_date = timezone.now()
        user.save()
        user, _ = attendee_testutils.create_test_user('attendee@example.com')
        Attendee.objects.create(user=user, event=Event.objects.current_event())
        user, _ = attendee_testutils.create_test_user('inactive@example.com')
        user.is_active = False
        user.save()
        Attendee.objects.create(user=user, event=Event.objects.current_event())
        user, _ = attendee_testutils.create_test_user(
            'draftspeaker@example.com')
        speaker = Speaker.objects.create(
            user=user,
            name='Test Speaker',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        Talk.objects.create(
            draft_speaker=speaker, title='Test', abstract='Test abstract',
            remarks='Test remarks', event=Event.objects.current_event()
        )
        user, _ = attendee_testutils.create_test_user(
            'inactivedraftspeaker@example.com')
        user.is_active = False
        user.save()
        speaker = Speaker.objects.create(
            user=user,
            name='Inactive Test Speaker',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        Talk.objects.create(
            draft_speaker=speaker, title='Test 2', abstract='Test abstract',
            remarks='Test remarks', event=Event.objects.current_event()
        )
        user, _ = attendee_testutils.create_test_user('speaker@example.com')
        speaker = Speaker.objects.create(
            user=user,
            name='Test Speaker',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        published_speaker = PublishedSpeaker.objects.copy_from_speaker(
            speaker, Event.objects.current_event())
        Talk.objects.create(
            published_speaker=published_speaker, title='Test',
            abstract='Test abstract',
            remarks='Test remarks', event=Event.objects.current_event()
        )

    def test_form_choices(self):
        self.assertEquals(len(self.recipients.get_form_choices()), 5,
                          'should have five options')

    def test_choice_label_invalid(self):
        with self.assertRaises(ValidationError):
            self.recipients.get_choice_label('invalid')

    def test_email_addresses_invalid(self):
        with self.assertRaises(ValidationError):
            self.recipients.get_email_addresses('invalid')

    def test_email_addresses_users(self):
        addrs = self.recipients.get_email_addresses('users')
        self.assertNotIn(settings.ADMINUSER_EMAIL, addrs)
        self.assertIn('contact@example.com', addrs)
        self.assertIn('attendee@example.com', addrs)
        self.assertNotIn('nocontact@example.com', addrs)
        self.assertNotIn('draftspeaker@example.com', addrs)
        self.assertNotIn('inactivedraftspeaker@example.com', addrs)
        self.assertNotIn('speaker@example.com', addrs)

    def test_email_addresses_attendees(self):
        addrs = self.recipients.get_email_addresses('attendees')
        self.assertNotIn(settings.ADMINUSER_EMAIL, addrs)
        self.assertNotIn('contact@example.com', addrs)
        self.assertIn('attendee@example.com', addrs)
        self.assertNotIn('inactive@example.com', addrs)
        self.assertNotIn('nocontact@example.com', addrs)
        self.assertNotIn('draftspeaker@example.com', addrs)
        self.assertNotIn('inactivedraftspeaker@example.com', addrs)
        self.assertNotIn('speaker@example.com', addrs)

    def test_email_addresses_inactive_attendees(self):
        addrs = self.recipients.get_email_addresses('inactive_attendees')
        self.assertNotIn(settings.ADMINUSER_EMAIL, addrs)
        self.assertNotIn('contact@example.com', addrs)
        self.assertNotIn('attendee@example.com', addrs)
        self.assertIn('inactive@example.com', addrs)
        self.assertNotIn('nocontact@example.com', addrs)
        self.assertNotIn('draftspeaker@example.com', addrs)
        self.assertNotIn('inactivedraftspeaker@example.com', addrs)
        self.assertNotIn('speaker@example.com', addrs)

    def test_email_addresses_draft_speakers(self):
        addrs = self.recipients.get_email_addresses('draft_speakers')
        self.assertNotIn(settings.ADMINUSER_EMAIL, addrs)
        self.assertNotIn('contact@example.com', addrs)
        self.assertNotIn('attendee@example.com', addrs)
        self.assertNotIn('nocontact@example.com', addrs)
        self.assertIn('draftspeaker@example.com', addrs)
        self.assertNotIn('inactivedraftspeaker@example.com', addrs)
        self.assertNotIn('speaker@example.com', addrs)

    def test_email_addresses_published_speakers(self):
        addrs = self.recipients.get_email_addresses('published_speakers')
        self.assertNotIn(settings.ADMINUSER_EMAIL, addrs)
        self.assertNotIn('contact@example.com', addrs)
        self.assertNotIn('attendee@example.com', addrs)
        self.assertNotIn('nocontact@example.com', addrs)
        self.assertNotIn('draftspeaker@example.com', addrs)
        self.assertNotIn('inactivedraftspeaker@example.com', addrs)
        self.assertIn('speaker@example.com', addrs)


class SendEmailViewTest(TestCase):
    def setUp(self):
        dev_data = DevData()
        dev_data.create_admin_user()
        self.url = reverse_lazy('send_email')

    def test_anonymous_access(self):
        r = self.client.get(self.url)
        self.assertRedirects(r, f'/accounts/login/?next={self.url}',
                             status_code=302)

    def test_send_some_mail_to_myself(self):
        mail.outbox = []
        self.client.login(username=settings.ADMINUSER_EMAIL,
                          password='admin')
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 200, 'get should return the form')

        r = self.client.post(
            self.url, data={
                'recipients': 'users',
                'subject': 'a message to all users',
                'body': '<p>a single sentence as the <b>message</b>.',
            }
        )
        self.assertEquals(len(mail.outbox), 1, 'should have one message')
        msg = mail.outbox[0]
        self.assertIsInstance(msg, DevDayEmailMessage)
        self.assertEquals(msg.subject, 'a message to all users')
        self.assertIn('a single sentence as the **message**.', msg.body)
        self.assertEquals(len(msg.alternatives), 1,
                          'should have one alternative')
        self.assertEquals(len(msg.alternatives[0]), 2,
                          'alternative should have two elements')
        self.assertEquals(
            msg.alternatives[0][0],
            '<p>a single sentence as the <b>message</b>.')
        self.assertEquals(msg.alternatives[0][1], 'text/html')

        self.assertNotIn(settings.DEFAULT_FROM_EMAIL, msg.recipients())
        self.assertIn(settings.ADMINUSER_EMAIL, msg.recipients())

    def test_send_mail_to_all_attendees(self):
        mail.outbox = []
        self.client.login(username=settings.ADMINUSER_EMAIL,
                          password='admin')

        attendee_testutils.create_test_user('nocontact@example.com')
        user, _ = attendee_testutils.create_test_user('contact@example.com')
        user.contact_permission_date = timezone.now()
        user.save()
        user, _ = attendee_testutils.create_test_user('attendee@example.com')
        Attendee.objects.create(user=user, event=Event.objects.current_event())

        r = self.client.post(
            self.url, data={
                'recipients': 'users',
                'subject': 'a message to all users',
                'body': '<p>a single sentence as the <b>message</b>.',
                'sendreal': '',
            }
        )

        self.assertEquals(len(mail.outbox), 1, 'should have one message')
        msg = mail.outbox[0]
        self.assertNotIn(settings.ADMINUSER_EMAIL, msg.recipients())
        self.assertIn('contact@example.com', msg.recipients())
        self.assertIn('attendee@example.com', msg.recipients())
        self.assertNotIn('nocontact@example.com', msg.recipients())
