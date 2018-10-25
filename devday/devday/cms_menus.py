from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from menus.base import Menu, NavigationNode
from menus.menu_pool import menu_pool

import talk
from event.models import Event


# It appears Django CMS has no easy way to add menu items in an ordered
# way when using multiple register_menu classes.  To get the desired order,
# this class contains all the menus across all applications.

@menu_pool.register_menu
class DevDayMenu(Menu):
    def get_nodes(self, request):
        entries = []

        event = Event.objects.current_event()
        if event and event.published and event.sessions_published:
            entries.append(
                NavigationNode(_('Sessions'), event.get_absolute_url(),
                               1))

        archive = NavigationNode(_('Archive'), '#', 50)
        events = Event.objects.filter(end_time__lt=timezone.now())
        if not request.user.is_staff:
            events = events.filter(published=True, sessions_published=True)
        events = events.exclude(id=Event.objects.current_event_id())
        for event in events.order_by('start_time'):
            archive.children.append(
                NavigationNode(event.title, event.get_absolute_url(),
                               event.id))
        entries.append(archive)

        if request.user.is_authenticated:
            profile = NavigationNode(
                _('Profile'), '#', 60, attr={'icon': 'fa-user'})
            profile.children.append(
                NavigationNode(_('Settings'), reverse('user_profile'), 1))
            if request.user.speaker:
                profile.children.append(
                    NavigationNode(_('Speaker Profile'),
                                   reverse('user_speaker_profile'), 1))
            if request.user.groups.filter(name=talk.COMMITTEE_GROUP).exists():
                profile.children.append(
                    NavigationNode(_('Program Committee'),
                                   reverse('talk_overview'),
                                   2))
            profile.children.append(
                NavigationNode(_('Logout'), reverse('auth_logout'), 1))

            entries.append(profile)
        else:
            entries.append(
                NavigationNode(_('Login'), reverse('auth_login'), 99))
        return entries
