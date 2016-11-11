from django.test import TestCase

from attendee.models import DevDayUser


class AttendeeProfileViewTest(TestCase):
    """
    Tests for attendee.views.AttendeeProfileView

    """

    def test_needs_login(self):
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/accounts/profile/')

    def test_used_template(self):
        DevDayUser.objects.create_user('test@example.org', 's3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'attendee/profile.html')
