from __future__ import unicode_literals

from django.core import mail
from django.test import TestCase

from attendee.models import DevDayUser, Attendee

ADMIN_EMAIL = 'admin@example.org'
ADMIN_PASSWORD = 'sUp3rS3cr3t'
USER_EMAIL = 'test@example.org'
USER_PASSWORD = 's3cr3t'


class DevDayUserManagerTest(TestCase):
    """
    Tests for attendee.models.DevDayUserManager.

    """

    def test_manager_create_user(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password(USER_PASSWORD))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_manager_create_superuser(self):
        user = DevDayUser.objects.create_superuser(ADMIN_EMAIL, ADMIN_PASSWORD)
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password(ADMIN_PASSWORD))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_manager_enforce_email(self):
        with self.assertRaises(ValueError) as error_context:
            DevDayUser.objects.create_user(None)
        self.assertEqual(str(error_context.exception), 'The given email must be set')
        with self.assertRaises(ValueError) as error_context:
            DevDayUser.objects.create_user('')
        self.assertEqual(str(error_context.exception), 'The given email must be set')
        user = DevDayUser.objects.create_user('noemail')
        self.assertEqual(user.get_username(), 'noemail')

    def test_manager_create_superuser_force_staff(self):
        with self.assertRaises(ValueError) as error_context:
            DevDayUser.objects.create_superuser(ADMIN_EMAIL, ADMIN_PASSWORD, is_staff=False)
        self.assertEqual(str(error_context.exception), 'Superuser must have is_staff=True.')

    def test_manager_create_superuser_force_superuser(self):
        with self.assertRaises(ValueError) as error_context:
            DevDayUser.objects.create_superuser(ADMIN_EMAIL, ADMIN_PASSWORD, is_superuser=False)
        self.assertEqual(str(error_context.exception), 'Superuser must have is_superuser=True.')


class DevDayUserTest(TestCase):
    """
    Tests for attendee.models.DevDayUser.

    """

    def test_get_full_name(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        self.assertEqual(user.get_full_name(), '')
        user.first_name = 'Test'
        self.assertEqual(user.get_full_name(), 'Test')
        user.last_name = 'User'
        self.assertEqual(user.get_full_name(), 'Test User')

    def test_get_short_name(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        self.assertEqual(user.get_short_name(), '')
        user.last_name = 'User'
        self.assertEqual(user.get_short_name(), '')
        user.first_name = 'Test'
        self.assertEqual(user.get_short_name(), 'Test')

    def test_email_user(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        user.email_user('Test mail', 'Test mail body')
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(USER_EMAIL, email.recipients())
        self.assertEqual(email.subject, 'Test mail')
        self.assertEqual(email.body, 'Test mail body')

    def test___str__(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        self.assertEqual(str(user), USER_EMAIL)
        user.first_name = 'Test'
        user.last_name = 'User'
        self.assertEqual(str(user), "Test User <%s>" % USER_EMAIL)


class AttendeeTest(TestCase):
    """
    Tests for attendee.models.Attendee.

    """

    def test___str__(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD, first_name='Test', last_name='User')
        attendee = Attendee(user=user)
        self.assertEqual(str(attendee), "Test User")
