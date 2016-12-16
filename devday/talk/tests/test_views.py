from django.test import TestCase


class TestSubmitSessionView(TestCase):
    def test_submit_session_anonymous(self):
        response = self.client.get('/session/submit-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/submit_session.html')
