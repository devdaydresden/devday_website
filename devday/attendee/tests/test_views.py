import re
from urllib.parse import quote

from bs4 import BeautifulSoup
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from attendee.forms import AttendeeRegistrationForm, EventRegistrationForm, \
    DevDayUserRegistrationForm
from attendee.models import DevDayUser, Attendee
from attendee.tests import attendee_testutils
from attendee.views import AttendeeRegistrationView, DevDayUserRegistrationView
from event.models import Event
from event.tests import event_testutils
from speaker.models import PublishedSpeaker
from speaker.tests import speaker_testutils

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
    def setUp(self):
        self.event = event_testutils.create_test_event()
        self.url = '/{}/attendee/register/'.format(self.event.slug)
        self.register_existing_url = '/{}/attendee/register/success/'.format(
            self.event.slug)
        self.register_new_url = '/accounts/register/complete/'

    def test_get_email_context(self):
        request = HttpRequest()
        context = AttendeeRegistrationView(
            request=request, event=self.event).get_email_context('testkey')
        self.assertIn('event', context)
        self.assertEqual(context.get('event'), self.event)

    def test_register_minimum_fields(self):
        response = self.client.post(
            self.url, data={
                'email': 'test@example.org', 'password1': 's3cr3t',
                'password2': 's3cr3t'},
            follow=False)
        self.assertRedirects(response, self.register_new_url)
        user = DevDayUser.objects.get(email='test@example.org')
        self.assertIsInstance(user, DevDayUser)
        self.assertIsNone(user.contact_permission_date)
        self.assertFalse(user.is_active)
        attendees = user.attendees
        self.assertEqual(attendees.count(), 1)
        attendee = attendees.first()
        self.assertIsInstance(attendee, Attendee)
        self.assertEqual(attendee.event, self.event)
        self.assertEqual(len(mail.outbox), 1)

    def test_register_permit_contact(self):
        response = self.client.post(
            self.url, data={
                'email': 'test@example.org', 'password1': 's3cr3t',
                'password2': 's3cr3t', 'accept_general_contact': 'checked'},
            follow=False)
        self.assertRedirects(response, self.register_new_url)
        now = timezone.now()
        user = DevDayUser.objects.get(email='test@example.org')
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
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'django_registration/registration_form.html')
        self.assertIn('form', response.context)
        self.assertIsInstance(
            response.context['form'], AttendeeRegistrationForm)

    def test_get_with_existing_non_attendee(self):
        user = DevDayUser.objects.create_user('test@example.org', 'test')
        self.client.login(username='test@example.org', password='test')
        response = self.client.get(self.url)

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
        response = self.client.post(self.url)

        self.assertRedirects(response, self.register_existing_url)
        try:
            attendee = Attendee.objects.get(user=user, event=self.event)
        except Attendee.DoesNotExist:
            self.fail('Attendee expected')
        self.assertEqual(attendee.user, user)

    def test_get_with_existing_attendee(self):
        user = DevDayUser.objects.create_user('test@example.org', 'test')
        Attendee.objects.create(user=user, event=self.event)

        self.client.login(username='test@example.org', password='test')
        response = self.client.get(self.url)

        self.assertRedirects(response, self.register_existing_url)

    def test_post_with_existing_attendee(self):
        user = DevDayUser.objects.create_user('test@example.org', 'test')
        Attendee.objects.create(user=user, event=self.event)

        self.client.login(username='test@example.org', password='test')
        response = self.client.post(self.url)

        self.assertRedirects(response, self.register_existing_url)


class DevDayRegistrationViewTest(TestCase):
    def setUp(self):
        self.url = '/register/'
        self.register_new_url = '/accounts/register/complete/'

    def test_next_traverses_state_transitions(self):
        next_url = '/foo'
        # load form
        response = self.client.get('{}?next={}'.format(self.url, next_url))
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        self.assertEqual(data['next'], next_url)
        # post form with wrong data
        data.update({
            'email': 'test@example.org',
            'password1': 'bar',
            'password2': 'foo',
        })
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].cleaned_data
        self.assertEqual(data['next'], next_url)
        # post form with correct data
        data.update({
            'email': 'test@example.org',
            'password1': 's3cr3t',
            'password2': 's3cr3t',
        })
        response = self.client.post(self.url, data=data, follow=False)
        self.assertRedirects(response, '/accounts/register/complete/')
        # check for next URL in activation mail
        self.assertEqual(len(mail.outbox), 1)
        activation_mail = mail.outbox[0]
        self.assertIn('?next={}'.format(next_url), activation_mail.body)

    def test_get_email_context(self):
        request = HttpRequest()
        request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        request.POST.update(
            next='/foo', email='test@example.org', password1='s3cr3t',
            password2='s3cr3t')
        context = DevDayUserRegistrationView(
            request=request).get_email_context('testkey')
        self.assertIn('next', context)
        self.assertEqual(context['next'], '/foo')
        self.assertIn('scheme', context)
        self.assertEqual(context['scheme'], 'https')

    def test_get_initial(self):
        next_url = '/foo'
        # load form
        response = self.client.get('{}?next={}'.format(self.url, next_url))
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        self.assertEqual(data['next'], next_url)

    def test_register_minimum_fields(self):
        response = self.client.post(
            self.url, data={
                'email': 'test@example.org', 'password1': 's3cr3t',
                'password2': 's3cr3t'},
            follow=False)
        self.assertRedirects(response, self.register_new_url)
        user = DevDayUser.objects.get(email='test@example.org')
        self.assertIsInstance(user, DevDayUser)
        self.assertIsNone(user.contact_permission_date)
        self.assertFalse(user.is_active)
        attendees = user.attendees
        self.assertEqual(attendees.count(), 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_register_permit_contact(self):
        response = self.client.post(
            self.url, data={
                'email': 'test@example.org', 'password1': 's3cr3t',
                'password2': 's3cr3t', 'accept_general_contact': 'checked'},
            follow=False)
        self.assertRedirects(response, self.register_new_url)
        now = timezone.now()
        user = DevDayUser.objects.get(email='test@example.org')
        self.assertIsInstance(user, DevDayUser)
        self.assertIsNotNone(user.contact_permission_date)
        self.assertLessEqual(user.contact_permission_date, now)
        self.assertFalse(user.is_active)
        attendees = user.attendees
        self.assertEqual(attendees.count(), 0)

    def test_get_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'django_registration/registration_form.html')
        self.assertIn('form', response.context)
        self.assertIsInstance(
            response.context['form'], DevDayUserRegistrationForm)

    def test_get_with_existing_user_with_next(self):
        user, password = attendee_testutils.create_test_user()
        self.client.login(username=user.email, password=password)
        response = self.client.get(
            '{}?next=/foo'.format(self.url), follow=False)
        self.assertRedirects(response, '/foo', fetch_redirect_response=False)

    def test_get_with_existing_user_without_next(self):
        user, password = attendee_testutils.create_test_user()
        self.client.login(username=user.email, password=password)
        response = self.client.get(self.url)
        self.assertRedirects(response, '/', fetch_redirect_response=False)


class DevDayUserActivationViewTest(TestCase):
    def setUp(self):
        user, _ = attendee_testutils.create_test_user()
        user.is_active = False
        user.save()
        self.activation_key = DevDayUserRegistrationView().get_activation_key(
            user)

    def test_get_success_url_with_next(self):
        url = '/activate/{}/?next=/foo'.format(self.activation_key)
        response = self.client.get(url)
        self.assertRedirects(
            response, '/accounts/login/?next=/foo',
            fetch_redirect_response=False)

    def test_get_success_url_without_next(self):
        url = '/activate/{}/'.format(self.activation_key)
        response = self.client.get(url)
        self.assertRedirects(
            response, '/accounts/login/?next=/accounts/profile/',
            fetch_redirect_response=False)


class AttendeeActivationViewTest(TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()
        user, _ = attendee_testutils.create_test_user()
        user.is_active = False
        user.save()
        Attendee.objects.create(user=user, event=self.event)
        self.activation_key = DevDayUserRegistrationView().get_activation_key(
            user)
        self.url = '/{}/attendee/activate/{}/'.format(
            self.event.slug, self.activation_key)

    def test_dispatch_with_invalid_event(self):
        response = self.client.get('/{}/attendee/activate/{}/'.format(
            'wrong-event', self.activation_key))
        self.assertEqual(response.status_code, 404)

    def test_get_success_url(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            '/accounts/login/?next=/{}/attendee/register/success/'.format(
                self.event.slug), fetch_redirect_response=False)


class AttendeeCancelViewTest(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()
        self.url = reverse('attendee_cancel',
                           kwargs={'event': self.event.id})
        self.login_url = reverse('auth_login')
        self.user = DevDayUser.objects.create_user('test@example.org', 'test')
        self.attendee = Attendee.objects.create(
            user=self.user, event=self.event)

    def test_anonymous(self):
        r = self.client.get(self.url)
        self.assertRedirects(r, '{}?next={}'.format(self.login_url, self.url))

    def test_user(self):
        self.client.login(username='test@example.org', password='test')
        r = self.client.get(self.url)
        self.assertRedirects(r, reverse('user_profile'))
        self.assertEquals(
            Attendee.objects.filter(user=self.user, event=self.event).count(),
            0,
            'User should not be an attendee for current event')


class AttendeeDeleteViewTest(TestCase):
    def test_requires_login(self):
        r = self.client.get('/accounts/delete/')
        self.assertEquals(r.status_code, 302)
        self.assertRedirects(r, '/accounts/login/?next=/accounts/delete/')

    def test_delete_keeps_speaker(self):
        speaker, user, password = speaker_testutils.create_test_speaker()
        self.client.login(username=user.email, password=password)
        r = self.client.post('/accounts/delete/')
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r.url, '/')

        with self.assertRaises(DevDayUser.DoesNotExist):
            user.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            speaker.refresh_from_db()

    def test_delete_keeps_published_speaker(self):
        speaker, user, password = speaker_testutils.create_test_speaker()
        published_speaker = PublishedSpeaker.objects.copy_from_speaker(
            speaker, event_testutils.create_test_event())
        self.assertEqual(published_speaker.speaker_id, speaker.id)

        self.client.login(username=user.email, password=password)
        email = user.email
        r = self.client.post('/accounts/delete/')
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r.url, '/')

        with self.assertRaises(DevDayUser.DoesNotExist):
            user.refresh_from_db()
        with self.assertRaises(ObjectDoesNotExist):
            speaker.refresh_from_db()
        published_speaker.refresh_from_db()
        self.assertIsNone(published_speaker.speaker_id)
        self.assertEqual(published_speaker.email, email)

    def test_post_delete_with_attendee(self):
        user, password = attendee_testutils.create_test_user()
        attendee = Attendee.objects.create(
            user=user, event=event_testutils.create_test_event())

        self.client.login(username=user.email, password=password)
        r = self.client.post('/accounts/delete/')
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r.url, '/')

        with self.assertRaises(Attendee.DoesNotExist):
            attendee.refresh_from_db()
        with self.assertRaises(DevDayUser.DoesNotExist):
            user.refresh_from_db()

    def test_get_template(self):
        user, password = attendee_testutils.create_test_user()
        self.client.login(username=user.email, password=password)
        r = self.client.get('/accounts/delete/')
        self.assertTemplateUsed(r, 'attendee/devdayuser_confirm_delete.html')


class LoginOrRegisterViewTest(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()
        self.user = DevDayUser.objects.create_user('test@example.org', 'test')
        self.url = '/{}/attendee/join/'.format(self.event.slug)

    def test_anonymous(self):
        response = self.client.get(self.url)
        self.assertEquals(
            response.status_code, 200,
            'should retrieve data from {}'.format(self.url))

    def test_user(self):
        self.client.login(username='test@example.org', password='test')
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse(
                'attendee_registration',
                kwargs={'event': self.event.slug}),
            msg_prefix='should redirect to registration page')


class CSVViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_password = 'foo'
        cls.staff = DevDayUser.objects.create_user(
            'staff@example.com', cls.staff_password, is_staff=True)
        cls.user = DevDayUser.objects.create_user('test@example.org', 'test')
        cls.event = Event.objects.current_event()
        cls.test_event = event_testutils.create_test_event()

    def setUp(self):
        self.attendee = Attendee.objects.create(
            user=self.user, event=self.event)
        self.other_attendee = Attendee.objects.create(
            user=self.user, event=self.test_event)

    def login(self):
        self.client.login(
            username=self.staff.email, password=self.staff_password)

    def get_anonymous(self, rev):
        url = reverse(rev)
        r = self.client.get(url)
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r.url, '/accounts/login/?next={}'.format(url),
                          'should redirect to login page')

    def get_staff(self, rev):
        url = reverse(rev)
        self.login()
        r = self.client.get(url)
        self.assertEquals(r.status_code, 200,
                          'should retrieve data from {}'.format(url))
        return r

    def test_get_attendees_anonymous(self):
        self.get_anonymous('admin_csv_attendees')

    def test_get_attendees_staff(self):
        self.login()
        r = self.get_staff('admin_csv_attendees')
        self.assertIn(self.user.email, r.content.decode(),
                      'user should be listed in attendees')

        self.attendee.delete()
        r = self.get_staff('admin_csv_attendees')
        self.assertNotIn(self.user.email, r.content.decode(),
                         'user should not be listed in attendees')

    def test_get_inactive_anonymous(self):
        self.get_anonymous('admin_csv_inactive')

    def test_get_inactive_staff(self):
        self.login()

        self.user.is_active = True
        self.user.save()
        r = self.get_staff('admin_csv_inactive')
        self.assertNotIn(self.user.email, r.content.decode(),
                         'user should not be listed in inactive')

        self.user.is_active = False
        self.user.save()
        r = self.get_staff('admin_csv_inactive')
        self.assertIn(self.user.email, r.content.decode(),
                      'user should be listed in inactive')

    def test_get_maycontact_anonymous(self):
        self.get_anonymous('admin_csv_maycontact')

    def test_get_maycontact_staff(self):
        self.login()

        self.user.contact_permission_date = timezone.now()
        self.user.save()
        r = self.get_staff('admin_csv_maycontact')
        self.assertIn(self.user.email, r.content.decode(),
                      'user should be listed in maycontact')

        self.user.contact_permission_date = None
        self.user.save()
        r = self.get_staff('admin_csv_maycontact')
        self.assertIn(self.user.email, r.content.decode(),
                      'user should be listed in maycontact')

        self.user.contact_permission_date = timezone.now()
        self.attendee.delete()
        self.user.save()
        r = self.get_staff('admin_csv_maycontact')
        self.assertIn(self.user.email, r.content.decode(),
                      'user should be listed in maycontact')

        self.user.contact_permission_date = None
        self.user.save()
        r = self.get_staff('admin_csv_maycontact')
        self.assertNotIn(self.user.email, r.content.decode(),
                         'user should not be listed in maycontact')


class CheckInAttendeeViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = event_testutils.create_test_event()
        cls.url = reverse('attendee_checkin', kwargs={'event': cls.event.slug})
        cls.staff, cls.staff_password = attendee_testutils.create_test_user(
            'staff@example.com', is_staff=True)
        cls.user, _ = attendee_testutils.create_test_user()
        cls.attendee = Attendee.objects.create(user=cls.user, event=cls.event)
        cls.other_attendee = Attendee.objects.create(
            user=cls.user, event=event_testutils.create_test_event('Other'))

    def setUp(self):
        self.attendee.checked_in = None

    def login(self):
        self.client.login(
            username=self.staff.email, password=self.staff_password)

    def test_get_anonymous(self):
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 302)
        self.assertEquals(
            r.url, '/accounts/login/?next={}'.format(self.url),
            'should redirect to login page')

    def test_get_staff(self):
        self.login()
        r = self.client.get(self.url)
        self.assertEquals(r.status_code, 200, 'should retrieve form')

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
        cls.event = event_testutils.create_test_event()
        cls.staff, cls.staff_password = attendee_testutils.create_test_user(
            'staff@example.org', is_staff=True)
        cls.user, _ = attendee_testutils.create_test_user('test@example.org')
        cls.attendee = Attendee.objects.create(user=cls.user, event=cls.event)
        other_user, _ = attendee_testutils.create_test_user(
            'other@example.org')
        cls.other_attendee = Attendee.objects.create(
            user=other_user, event=event_testutils.create_test_event('Other'))

    def setUp(self):
        self.attendee.checked_in = None
        self.attendee.save()

    def _get_url(self, id, verification):
        return reverse(
            'attendee_checkin_url',
            kwargs={'id': id, 'verification': verification,
                    'event': self.event.slug}
        )

    def _get_url_for_attendee(self, attendee):
        return self._get_url(attendee.id, attendee.get_verification())

    def _get_code(self, r):
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
        url = self._get_url_for_attendee(self.attendee)
        r = self.client.get(url)
        self.assertEquals(r.status_code, 302)
        self.assertEquals(
            r.url, '/accounts/login/?next={}'.format(quote(quote(url))),
            'should redirect to login page')

    def test_get_staff(self):
        url = self._get_url(12345678, 'somestring')
        self.login()
        r = self.client.get(url)
        self.assertEquals(
            r.status_code, 200, 'should retrieve form')
        self.assertEquals(
            self._get_code(r), 'invalid', 'code should be invalid')

    def test_get_valid(self):
        url = self._get_url_for_attendee(self.attendee)
        self.login()
        r = self.client.get(url)
        self.assertEquals(
            r.status_code, 200, 'should retrieve form')
        self.assertEquals(
            self._get_code(r), 'OK', 'should get checked in')

    def test_get_checked_in(self):
        url = self._get_url_for_attendee(self.attendee)
        self.attendee.check_in()
        self.attendee.save()
        self.login()
        r = self.client.get(url)
        self.assertEquals(
            r.status_code, 200, 'should retrieve form')
        self.assertEquals(
            self._get_code(r), 'already',
            'atteendee should be checked in already')

    def test_get_not_registered(self):
        url = self._get_url(
            12345678, Attendee.objects.get_verification(12345678))
        self.login()
        r = self.client.get(url)
        self.assertEquals(
            r.status_code, 200, 'should retrieve form')
        self.assertEquals(
            self._get_code(r), 'notfound', 'atteendee should not be found')

    def test_get_otherevent(self):
        url = self._get_url_for_attendee(self.other_attendee)
        self.login()
        r = self.client.get(url)
        self.assertEquals(
            r.status_code, 200, 'should retrieve form')
        self.assertEquals(
            self._get_code(r), 'wrongevent', 'code should be for wrong event')


class CheckInAttendeeViewQRCodeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = event_testutils.create_test_event()
        cls.url = reverse(
            'attendee_checkin_qrcode', kwargs={'event': cls.event.slug})
        cls.user, cls.user_password = attendee_testutils.create_test_user(
            'testqrcode@example.org')
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
        self.assertEquals(
            r.status_code, 200, 'should retrieve form')
        self.assertEquals(
            self.get_code(r), 'notregistered',
            'attendee should not be registered for current event')

    def test_get_qrcode_current_event(self):
        attendee = Attendee.objects.create(
            user=self.user, event=self.event)
        self.login()
        response = self.client.get(self.url)
        self.assertEquals(
            response.status_code, 200, 'should retrieve form')
        self.assertEquals(
            self.get_code(response), 'OK',
            ('attendee should be registered for current event and not checked'
             ' in yet'))
        self.assertContains(response, attendee.get_checkin_url(self.event))

    def test_get_qrcode_current_event_checkedin(self):
        attendee = Attendee.objects.create(
            user=self.user, event=self.event, checked_in=timezone.now())
        self.login()
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200,
                          'should retrieve form')
        self.assertEquals(self.get_code(response), 'already',
                          'attendee should be already checked in')
        self.assertNotContains(response, attendee.get_checkin_url(self.event))
