from django.core import mail
from django.test import TestCase, override_settings

from event.models import Event
from sponsoring.forms import SponsoringContactForm
from sponsoring.models import SponsoringPackage


@override_settings(ROOT_URLCONF='sponsoring.tests.urls')
class SponsoringViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.current_event()
        package1 = SponsoringPackage.objects.create(
            package_type=1, pricing='500 €', event=cls.event)
        package2 = SponsoringPackage.objects.create(
            package_type=2, pricing='1000 €', event=cls.event)
        package3 = SponsoringPackage.objects.create(
            package_type=3, pricing='1500 €', event=cls.event)
        package1.sponsoringpackageitem_set.create(
            name='Bronze 1', is_header=True)
        package1.sponsoringpackageitem_set.create(name='Bronze Nice')
        package1.sponsoringpackageitem_set.create(name='Bronze so wow')
        package1.sponsoringpackageitem_set.create(name='Fine Bronze')
        package2.sponsoringpackageitem_set.create(
            name='Silver 1', is_header=True)
        package2.sponsoringpackageitem_set.create(name='Silver Nice')
        package2.sponsoringpackageitem_set.create(name='Silver so wow')
        package2.sponsoringpackageitem_set.create(name='Fine Silver')
        package3.sponsoringpackageitem_set.create(
            name='Gold 1', is_header=True)
        package3.sponsoringpackageitem_set.create(name='Gold Nice')
        package3.sponsoringpackageitem_set.create(name='Gold so wow')
        package3.sponsoringpackageitem_set.create(name='Fine Gold')

    def setUp(self):
        self.url = '/sponsoring/{}/'.format(self.event.slug)

    def test_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sponsoring/sponsoring.html')

    def test_get_context_data(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIn('form', context)
        self.assertIsInstance(context['form'], SponsoringContactForm)
        self.assertIn('packages', context)
        self.assertEqual(len(context['packages']), 3)
        for package_parts in context['packages']:
            self.assertEqual(len(package_parts['package_items']), 1)
            for package_item in package_parts['package_items']:
                self.assertEqual(len(package_item['package_items']), 3)

    def test_post_renders_template_on_form_error(self):
        data = {'email': 'test'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(len(response.context['form'].errors) > 0)
        self.assertTemplateUsed(response, 'sponsoring/sponsoring.html')

    def test_post_redirects_and_sends_mail_on_form_valid(self):
        organization = 'Acme Inc.'
        email = 'test@example.org'
        body_text = 'So nice packages, much money, so wow!'
        data = {
            'organization': organization, 'email': email, 'body': body_text}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, '/sponsoring/thanks/')
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(self.event.title, message.subject)
        self.assertIn(organization, message.subject)
        self.assertIn(organization, message.body)
        self.assertIn(body_text, message.body)
        self.assertEqual(message.reply_to, [email])


@override_settings(ROOT_URLCONF='sponsoring.tests.urls')
class SponsoringThanksViewTest(TestCase):
    def test_template(self):
        response = self.client.get('/sponsoring/thanks/')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'sponsoring/sponsoring_thanks.html')


@override_settings(ROOT_URLCONF='sponsoring.tests.urls')
class RedirectToCurrentEventViewTest(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()

    def test_redirect_to_event_page(self):
        response = self.client.get('/sponsoring/')
        self.assertRedirects(
            response, '/sponsoring/{}/'.format(self.event.slug),
            fetch_redirect_response=False)
