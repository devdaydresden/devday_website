from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from menus.base import Menu, NavigationNode
from menus.menu_pool import menu_pool

from .models import Event


@menu_pool.register_menu
class EventArchiveMenu(Menu):
    def get_nodes(self, request):
        archive = NavigationNode(_('Archive'), '#', 0)
        events = Event.objects.filter(end_time__lt=timezone.now())
        if not request.user.is_staff:
            events = events.filter(published=True, sessions_published=True)
        events = events.exclude(id=Event.objects.current_event_id())
        for event in events.order_by('start_time'):
            archive.children.append(
                NavigationNode(event.title, event.get_absolute_url(),
                               event.id))
        return [archive]


@menu_pool.register_menu
class EventSessionMenu(Menu):
    def get_nodes(self, request):
        event = Event.objects.current_event()
        entries = []
        if event and event.published and event.sessions_published:
            entries.append(
                NavigationNode(_('Sessions'), event.get_absolute_url(),
                               event.id))
        return entries
