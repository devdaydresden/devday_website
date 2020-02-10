from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse

from attendee.models import Attendee
from attendee.tests.attendee_testutils import create_test_user
from devday import cms_menus
from devday.utils.devdata import DevData
from event.models import Event
from menus.menu_pool import menu_pool

CLASS_UNDER_TEST = "DevDayMenu"


def filter_nodes_by_namespace(nodes, namespace):
    for n in nodes[:]:
        if n.namespace != namespace:
            nodes.remove(n)
    return nodes


def get_nodes(user=None):
    request = RequestFactory().get("/")
    request.user = user if user else AnonymousUser()
    with patch("menus.menu_pool.use_draft", return_value=False):
        renderer = menu_pool.get_renderer(request)
    nodes = renderer.get_nodes()
    # There are other menu entries (CMSMenu etc.) and they would confuse these
    # tests, so filter them out.
    filter_nodes_by_namespace(nodes, CLASS_UNDER_TEST)
    return nodes


class DevDayMenuTest(TestCase):
    def setUp(self):
        self.devdata = DevData()
        self.devdata.create_admin_user()
        self.devdata.create_pages()
        self.devdata.update_events()
        self.event = Event.objects.current_event()

    def test_menu(self):
        entries = get_nodes()
        self.assertIn(cms_menus.USER_CAN_REGISTER, entries[0].attr)
        self.assertIn(cms_menus.SUBMISSION_OPEN, entries[1].attr)
        self.assertIn(cms_menus.SESSIONS_PUBLISHED, entries[2].attr)
        self.assertIn(cms_menus.CHILDREN, entries[3].attr)
        self.assertEqual(
            len(entries[3].children), 3, "Archive should have three children"
        )
        self.assertEqual(entries[4].url, reverse("auth_login"))

    def test_no_current(self):
        for event in Event.objects.all():
            event.published = False
            event.save()
        entries = get_nodes()
        self.assertEqual(len(entries), 1, "should have one entry")

    def test_registration_off(self):
        self.event.registration_open = False
        self.event.submission_open = True
        self.event.save()
        entries = get_nodes()
        self.assertIn(cms_menus.SUBMISSION_OPEN, entries[0].attr)
        self.assertIn(cms_menus.SESSIONS_PUBLISHED, entries[1].attr)

    def test_submission_off(self):
        self.event.registration_open = True
        self.event.submission_open = False
        self.event.save()
        entries = get_nodes()
        self.assertIn(cms_menus.USER_CAN_REGISTER, entries[0].attr)
        self.assertIn(cms_menus.SESSIONS_PUBLISHED, entries[1].attr)

    def test_logged_in(self):
        (user, _) = create_test_user()
        Attendee.objects.filter(user=user, event=self.event).delete()
        entries = get_nodes(user=user)
        self.assertEqual(entries[4].url, "#")
        children = entries[4].children
        self.assertEqual(children[0].url, reverse("user_profile"))
        self.assertEqual(children[1].url, reverse("auth_logout"))

        Attendee.objects.create(user=user, event=self.event)
        entries = get_nodes(user=user)
        self.assertEqual(entries[3].url, "#")
        children = entries[3].children
        self.assertEqual(len(children), 3, "profile menu should have three entries")
        self.assertEqual(children[0].url, reverse("user_profile"))
        self.assertEqual(
            children[1].url,
            reverse("attendee_checkin_qrcode", kwargs={"event": self.event.slug}),
        )
        self.assertEqual(children[2].url, reverse("auth_logout"))
