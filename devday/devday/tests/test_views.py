from django.contrib.auth.models import Group
from django.test import TestCase

from attendee.models import Attendee
from attendee.tests import attendee_testutils
from devday.utils.devdata import DevData
from event.models import Event
from speaker.tests import speaker_testutils


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