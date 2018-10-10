import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from django.core import mail
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from attendee.forms import AttendeeRegistrationForm, EventRegistrationForm
from attendee.models import DevDayUser, Attendee
from attendee.views import AttendeeRegistrationView
from event.models import Event
from event.test.testutils import create_test_event
from talk.tests.testutils import create_test_speaker, create_test_talk

ADMIN_EMAIL = 'admin@example.org'
ADMIN_PASSWORD = 'sUp3rS3cr3t'
USER_EMAIL = 'test@example.org'
USER_PASSWORD = 's3cr3t'


class AttendeeProfileViewTest(TestCase):
    """
    Tests for attendee.views.AttendeeProfileView

    """

    def test_needs_login(self):
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
                         '/accounts/login/?next=/accounts/profile/')

    def test_used_template(self):
        DevDayUser.objects.create_user('test@example.org', 's3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'attendee/profile.html')


class AttendeeRegistrationViewTest(TestCase):
    def test_get_email_context(self):
        request = HttpRequest()
        context = AttendeeRegistrationView(request=request).get_email_context(
            'testkey')
        self.assertIn('request', context)
        self.assertEqual(context.get('request'), request)

    def test_register_minimum_fields(self):
        form = AttendeeRegistrationForm(
            data={'email': 'test@example.org', 'password1': 's3cr3t',
                  'password2': 's3cr3t'})
        valid = form.is_valid()
        self.assertTrue(valid, form.errors)

        request = HttpRequest()
        view = AttendeeRegistrationView(request=request)
        user = view.register(form)

        self.assertIsInstance(user, DevDayUser)
        self.assertIsNone(user.contact_permission_date)
        self.assertFalse(user.is_active)

        attendees = user.attendees
        self.assertEqual(attendees.count(), 1)
        attendee = attendees.first()
        self.assertIsInstance(attendee, Attendee)
        self.assertIsNotNone(attendee.event)

        self.assertEqual(len(mail.outbox), 1)

    def test_register_permit_contact(self):
        form = AttendeeRegistrationForm(
            data={'email': 'test@example.org', 'password1': 's3cr3t',
                  'password2': 's3cr3t', 'accept_general_contact': 'checked',
                  'accept_devday_contact': 'checked'})
        valid = form.is_valid()
        self.assertTrue(valid, form.errors)

        request = HttpRequest()
        view = AttendeeRegistrationView(request=request)
        user = view.register(form)
        now = timezone.now()

        self.assertIsInstance(user, DevDayUser)
        self.assertIsNotNone(user.contact_permission_date)
        self.assertLessEqual(user.contact_permission_date, now)
        self.assertFalse(user.is_active)

        attendees = user.attendees
        self.assertEqual(attendees.count(), 1)

        attendee = attendees.first()
        self.assertIsInstance(attendee, Attendee)

        self.assertEqual(len(mail.outbox), 1)

    def test_get_anonymous(self):
        response = self.client.get(reverse('registration_register'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'django_registration/registration_form.html')
        self.assertIn('form', response.context)
        self.assertIsInstance(
            response.context['form'], AttendeeRegistrationForm)

    def test_get_with_existing_non_attendee(self):
        user = DevDayUser.objects.create_user('test@example.org', 'test')
        self.client.login(username='test@example.org', password='test')
        response = self.client.get(reverse('registration_register'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'django_registration/registration_form.html')
        self.assertIn('form', response.context)
        self.assertIsInstance(
            response.context['form'], EventRegistrationForm)
        self.assertIn('user', response.context)
        self.assertEqual(response.context['user'], user)

    def test_post_with_existing_non_attendee(self):
        user = DevDayUser.objects.create_user('test@example.org', 'test')
        self.client.login(username='test@example.org', password='test')
        response = self.client.post(reverse('registration_register'))

        self.assertRedirects(response, reverse('register_success'))
        try:
            attendee = Attendee.objects.get(
                user=user, event=Event.objects.current_event())
        except Attendee.DoesNotExist:
            self.fail('Attendee expected')
        self.assertEqual(attendee.user, user)

    def test_get_with_existing_attendee(self):
        user = DevDayUser.objects.create_user('test@example.org', 'test')
        Attendee.objects.create(user=user, event=Event.objects.current_event())

        self.client.login(username='test@example.org', password='test')
        response = self.client.get(reverse('registration_register'))

        self.assertRedirects(response, reverse('register_success'))

    def test_post_with_existing_attendee(self):
        user = DevDayUser.objects.create_user('test@example.org', 'test')
        Attendee.objects.create(user=user, event=Event.objects.current_event())

        self.client.login(username='test@example.org', password='test')
        response = self.client.post(reverse('registration_register'))

        self.assertRedirects(response, reverse('register_success'))


class AttendeeDeleteViewTest(TestCase):
    def setUp(self):
        self.user = DevDayUser.objects.create_user('test@example.org', 'test')

    def test_requires_login(self):
        r = self.client.get('/accounts/delete/')
        self.assertEquals(r.status_code, 302)
        self.assertRedirects(r, '/accounts/login/?next=/accounts/delete/')

    def test_cannot_delete_speaker_with_talk(self):
        attendee = Attendee.objects.create(user=self.user,
                                           event=create_test_event())
        speaker = create_test_speaker(attendee)
        create_test_talk(speaker)

        self.client.login(username='test@example.org', password='test')
        r = self.client.post('/accounts/delete/')
        self.assertEquals(r.status_code, 409)

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.id)

    def test_can_delete_speaker_without_talk(self):
        attendee = Attendee.objects.create(user=self.user,
                                           event=create_test_event())
        create_test_speaker(attendee)

        self.client.login(username='test@example.org', password='test')
        r = self.client.post('/accounts/delete/')
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r.url, '/')

        with self.assertRaises(DevDayUser.DoesNotExist):
            self.user.refresh_from_db()

    def test_post_delete_with_attendee(self):
        attendee = Attendee.objects.create(user=self.user,
                                           event=create_test_event())

        self.client.login(username='test@example.org', password='test')
        r = self.client.post('/accounts/delete/')
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r.url, '/')

        with self.assertRaises(Attendee.DoesNotExist):
            attendee.refresh_from_db()
        with self.assertRaises(DevDayUser.DoesNotExist):
            self.user.refresh_from_db()

    def test_get_template(self):
        self.client.login(username='test@example.org', password='test')
        r = self.client.get('/accounts/delete/')
        self.assertTemplateUsed(r, 'attendee/devdayuser_confirm_delete.html')


class AttendeeListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('admin_csv_attendees')
        cls.staff_password = 'foo'
        cls.staff = DevDayUser.objects.create_user(
            'staff@example.com', cls.staff_password, is_staff=True)
        cls.user = DevDayUser.objects.create_user('test@example.org', 'test')
        cls.attendee = Attendee.objects.create(
            user=cls.user, event=Event.objects.current_event())
        cls.other_attendee = Attendee.objects.create(
            user=cls.user, event=create_test_event())

    def login(self):
        self.client.login(
            username=self.staff.email, password=self.staff_password)

    def test_get_anonymous(self):
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r.url, '/accounts/login/?next={}'.format(self.url),
                          'should redirect to login page')

    def test_get_staff(self):
        self.login()
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve data')


class CheckInAttendeeViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('attendee_checkin')
        cls.staff_password = 'foo'
        cls.staff = DevDayUser.objects.create_user(
            'staff@example.com', cls.staff_password, is_staff=True)
        cls.user = DevDayUser.objects.create_user('test@example.org', 'test')
        cls.attendee = Attendee.objects.create(
            user=cls.user, event=Event.objects.current_event())
        cls.other_attendee = Attendee.objects.create(
            user=cls.user, event=create_test_event())

    def setUp(self):
        self.attendee.checked_in = None

    def login(self):
        self.client.login(
            username=self.staff.email, password=self.staff_password)

    def test_get_anonymous(self):
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r.url, '/accounts/login/?next={}'.format(self.url),
                          'should redirect to login page')

    def test_get_staff(self):
        self.login()
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')

    def test_post_empty(self):
        self.login()
        r = self.client.post(self.url, data={})
        self.assertEquals(r.status_code, 200, 'should not redirect')
        # FIXME attendee never changes over here, but does in the view
        # self.assertIsNone(self.attendee.checked_in,
        #                   'attendee should not be checked in')

    def test_post_checkin_code(self):
        self.login()
        r = self.client.post(
            self.url, data={'attendee': self.attendee.checkin_code})
        self.assertEquals(r.status_code, 302, 'should redirect to self')
        self.assertEquals(r.url, self.url, 'should redirect to self')
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        # FIXME attendee never changes over here, but does in the view
        # self.assertIsNotNone(self.attendee.checked_in,
        #                      'attendee should be checked in')

    def test_post_email(self):
        self.login()
        r = self.client.post(
            self.url, data={'attendee': self.attendee.user.email})
        self.assertEquals(r.status_code, 302, 'should redirect to self')
        self.assertEquals(r.url, self.url, 'should redirect to self')
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        # FIXME attendee never changes over here, but does in the view
        # self.assertIsNotNone(self.attendee.checked_in,
        #                      'attendee should be checked in')


class CheckInAttendeeViewUrlTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_password = 'foo'
        cls.staff = DevDayUser.objects.create_user(
            'staff@example.com', cls.staff_password, is_staff=True)
        cls.user = DevDayUser.objects.create_user('test@example.org', 'test')
        cls.attendee = Attendee.objects.create(
            user=cls.user, event=Event.objects.current_event())
        cls.other_attendee = Attendee.objects.create(
            user=DevDayUser.objects.create_user('other@example.org', 'test'),
            event=create_test_event())

    def setUp(self):
        self.attendee.checked_in = None
        self.attendee.save()

    def get_url(self, id, verification):
        return reverse(
            'attendee_checkin_url',
            kwargs={'id': id, 'verification': verification}
            )

    def get_url_for_attendee(self, attendee):
        return self.get_url(attendee.id, attendee.get_verification())

    def get_code(self, r):
        s = BeautifulSoup(r.content, 'lxml')
        m = s.find(re.compile('.*'), {'id': 'checkin_result'})
        if m:
            return m.get('data-code')
        else:
            return None

    def login(self):
        self.client.login(
            username=self.staff.email, password=self.staff_password)

    def test_get_anonymous(self):
        url = self.get_url_for_attendee(self.attendee)
        r = self.client.get(url)
        self.assertEquals(r.status_code, 302)
        self.assertEquals(
            r.url, '/accounts/login/?next={}'.format(quote(quote(url))),
            'should redirect to login page')

    def test_get_staff(self):
        url = self.get_url(12345678, 'somestring')
        self.login()
        r = self.client.get(url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        self.assertEquals(self.get_code(r), 'invalid',
                          ('code should be invalid'))

    def test_get_valid(self):
        url = self.get_url_for_attendee(self.attendee)
        self.login()
        r = self.client.get(url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        self.assertEquals(self.get_code(r), 'OK',
                          ('should get checked in'))

    def test_get_checked_in(self):
        url = self.get_url_for_attendee(self.attendee)
        self.attendee.check_in()
        self.attendee.save()
        self.login()
        r = self.client.get(url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        self.assertEquals(self.get_code(r), 'already',
                          ('atteendee should be checked in already'))

    def test_get_not_registered(self):
        url = self.get_url(12345678,
                           Attendee.objects.get_verification(12345678))
        self.login()
        r = self.client.get(url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        self.assertEquals(self.get_code(r), 'notfound',
                          ('atteendee should not be found'))

    def test_get_otherevent(self):
        url = self.get_url_for_attendee(self.other_attendee)
        self.login()
        r = self.client.get(url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        self.assertEquals(self.get_code(r), 'wrongevent',
                          ('code should be for wrong event'))


class CheckInAttendeeViewQRCodeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('attendee_checkin_qrcode')
        cls.user_password = 'test'
        cls.user = DevDayUser.objects.create_user(
            'testqrcode@example.org', cls.user_password)
        Attendee.objects.filter(user=cls.user).delete()

    def login(self):
        self.client.login(
            username=self.user.email, password=self.user_password)

    def get_code(self, r):
        s = BeautifulSoup(r.content, 'lxml')
        m = s.find(re.compile('.*'), {'id': 'qrcodemessage'})
        if m:
            return m.get('data-code')
        else:
            return None

    def test_get_anonymous(self):
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 302)
        self.assertEquals(
            r.url, '/accounts/login/?next={}'.format(quote(quote(self.url))),
            'should redirect to login page')

    def test_get_qrcode_no_current_event(self):
        self.login()
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        self.assertEquals(self.get_code(r), 'notregistered',
                          ('attendee should not be registered for'
                           ' current event'))

    def test_get_qrcode_current_event(self):
        self.attendee = Attendee.objects.create(
            user=self.user, event=Event.objects.current_event())
        self.login()
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        self.assertEquals(self.get_code(r), 'OK',
                          ('attendee should be registered for current event'
                           ' and not checked in yet'))
        self.assertContains(r, self.attendee.get_checkin_url())

    def test_get_qrcode_current_event_checkedin(self):
        self.attendee = Attendee.objects.create(
            user=self.user, event=Event.objects.current_event(),
            checked_in=timezone.now())
        self.login()
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve form')
        self.assertEquals(self.get_code(r), 'already',
                          'attendee should be already checked in')
        self.assertNotContains(r, self.attendee.get_checkin_url())
