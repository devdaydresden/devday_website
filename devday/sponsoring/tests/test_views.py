from django.test import TestCase, override_settings

from event.models import Event


@override_settings(ROOT_URLCONF='sponsoring.tests.urls')
class SponsoringViewTest(TestCase):
    pass


@override_settings(ROOT_URLCONF='sponsoring.tests.urls')
class SponsoringThanksViewTest(TestCase):
    def test_template(self):
        response = self.client.get('/sponsoring/thanks/')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'sponsoring/sponsoring.html')


@override_settings(ROOT_URLCONF='sponsoring.tests.urls')
class RedirectToCurrentEventViewTest(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()

    def test_redirect_to_event_page(self):
        response = self.client.get('/sponsoring/')
        self.assertRedirects(
            response, '/sponsoring/{}/'.format(self.event.slug),
            fetch_redirect_response=False)
