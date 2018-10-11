from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.test.client import RequestFactory
from menus.menu_pool import menu_pool

from devday.utils.devdata import DevData
from event.models import Event


# FIXME apparently there's a bug in django-cms 3.5.2: Django's
# user.is_authenticated has been a property since 1.10, but django-cms
# treats it as a callable.
#   File "/usr/local/lib/python3.6/site-packages/menus/menu_pool.py", line 243,
#       in get_renderer
#     return MenuRenderer(pool=self, request=request)
#   File "/usr/local/lib/python3.6/site-packages/menus/menu_pool.py", line 107,
#       in __init__
#     self.draft_mode_active = use_draft(request)
#   File "/usr/local/lib/python3.6/site-packages/cms/utils/moderator.py",
#       line 5, in use_draft
#     is_staff = (request.user.is_authenticated() and request.user.is_staff)
# TypeError: 'property' object is not callable

def get_register_menu(register_menu, request):
        request.user = AnonymousUser
        with patch('menus.menu_pool.use_draft', return_value=False):
            renderer = menu_pool.get_renderer(request)
        return menu_pool.menus[register_menu](renderer)


class EventArchiveMenuTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.devdata = DevData()
        cls.devdata.create_admin_user()
        cls.devdata.create_pages()
        cls.devdata.update_events()

    def test_menu(self):
        request = RequestFactory().get('/')
        menu = get_register_menu('EventArchiveMenu', request)
        entries = menu.get_nodes(request)
        self.assertEquals(
            len(entries), 1, 'should have one entry')
        self.assertEquals(
            len(entries[0].children), 2, 'should have two children')


class EventSessionMenuTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.devdata = DevData()
        cls.devdata.create_admin_user()
        cls.devdata.create_pages()
        cls.devdata.update_events()

    def test_menu(self):
        request = RequestFactory().get('/')
        menu = get_register_menu('EventSessionMenu', request)
        entries = menu.get_nodes(request)
        self.assertEquals(len(entries), 1, 'should have one entry')
        self.assertEquals(
            len(entries[0].children), 0, 'should have no children')

    def test_no_current(self):
        for event in Event.objects.all():
            event.published = False
            event.save()
        request = RequestFactory().get('/')
        menu = get_register_menu('EventSessionMenu', request)
        entries = menu.get_nodes(request)
        self.assertEquals(len(entries), 0, 'should have one entry')
