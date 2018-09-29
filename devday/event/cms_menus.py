from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from menus.base import Menu, NavigationNode
from menus.menu_pool import menu_pool

from .models import Event


@menu_pool.register_menu
class EventArchiveMenu(Menu):
    def get_nodes(self, request):
        archive = NavigationNode(_('Archive'), '#', 0)
        for event in Event.objects.filter(end_time__lt=timezone.now()).exclude(
                id=Event.objects.current_event_id()).order_by('start_time'):
            archive.children.append(
                NavigationNode(event.title, event.get_absolute_url(), event.id))
        return [archive]
