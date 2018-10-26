from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.test.client import RequestFactory
from menus.menu_pool import menu_pool

from devday.utils.devdata import DevData
from event.models import Event


def get_register_menu(register_menu, request):
        request.user = AnonymousUser()
        with patch('menus.menu_pool.use_draft', return_value=False):
            renderer = menu_pool.get_renderer(request)
        return menu_pool.menus[register_menu](renderer)


class EventSessionMenuTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.devdata = DevData()
        cls.devdata.create_admin_user()
        cls.devdata.create_pages()
        cls.devdata.update_events()
        cls.menu = 'DevDayMenu'

    def test_menu(self):
        request = RequestFactory().get('/')
        menu = get_register_menu(self.menu, request)
        entries = menu.get_nodes(request)
        self.assertEquals(len(entries), 6, 'should have one entry')
        self.assertEquals(
            len(entries[0].children), 0, 'should have no children')

    def test_no_current(self):
        for event in Event.objects.all():
            event.published = False
            event.save()
        request = RequestFactory().get('/')
        menu = get_register_menu(self.menu, request)
        entries = menu.get_nodes(request)
        self.assertEquals(len(entries), 3, 'should have three entries')
