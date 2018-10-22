from django.core.urlresolvers import reverse_lazy
from django.utils.translation import gettext_lazy as _
from menus.base import Menu, NavigationNode
from menus.menu_pool import menu_pool

from .models import Event


@menu_pool.register_menu
class AttendeeCheckinMenu(Menu):
    def get_nodes(self, request):
        event = Event.objects.current_event()
        if not request.user.is_staff or not event.sessions_published:
            return []
        return [NavigationNode(
            _('Check in'), reverse_lazy(
                'attendee_checkin', kwargs={'event': event.slug}), 99)]
