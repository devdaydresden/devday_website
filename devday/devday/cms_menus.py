from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from menus.base import Menu, Modifier, NavigationNode
from menus.menu_pool import menu_pool

from talk import COMMITTEE_GROUP
from event.models import Event


CAN_CHECK_IN = 'can_check_in'
IS_SPEAKER = 'is_speaker'
IS_COMMITTEE_MEMBER = 'is_committee_member'
IS_ATTENDEE = 'register_attendee'
SUBMISSION_OPEN = 'submission_open'
SESSIONS_PUBLISHED = 'sessions_published'


@menu_pool.register_modifier
class DevDayModifier(Modifier):
    def user_is_attendee(self, request, event):
        return event and event.published \
            and event.registration_open \
            and request.user.is_authenticated \
            and request.user.get_attendee(event) is not None

    def user_can_check_in(self, request, event):
        return (request.user.is_authenticated
                and request.user.get_attendee(event) is not None)

    def user_is_committee_member(self, request, event):
        return (request.user.is_authenticated
                and request.user.groups.filter(name=COMMITTEE_GROUP).exists())

    def prune_nodes(self, nodes, attr, fn, request, event):
        affected_nodes = list(
            filter(lambda n: attr in n.attr, nodes))
        if affected_nodes:
            b = fn(request, event)
            for n in affected_nodes:
                if b != n.attr[attr]:
                    nodes.remove(n)

    def prune_all_nodes(self, nodes, request, event):
        self.prune_nodes(nodes, CAN_CHECK_IN, self.user_can_check_in,
                         request, event)
        self.prune_nodes(nodes, IS_SPEAKER,
                         lambda r, e: hasattr(r.user, 'speaker'),
                         request, event)
        self.prune_nodes(nodes, IS_COMMITTEE_MEMBER,
                         self.user_is_committee_member,
                         request, event)
        self.prune_nodes(nodes, IS_ATTENDEE, self.user_is_attendee,
                         request, event)
        self.prune_nodes(nodes, SUBMISSION_OPEN,
                         lambda r, e: e.submission_open,
                         request, event)
        self.prune_nodes(nodes, SESSIONS_PUBLISHED,
                         lambda r, e: e.sessions_published,
                         request, event)
        for node in nodes:
            self.prune_all_nodes(node.children, request, event)

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if post_cut:
            event = Event.objects.current_event()
            self.prune_all_nodes(nodes, request, event)
        return nodes


# It appears Django CMS has no easy way to add menu items in an ordered
# way when using multiple register_menu classes.  To get the desired order,
# this class contains all the menus across all applications.

@menu_pool.register_menu
class DevDayMenu(Menu):
    def get_nodes(self, request):
        entries = []

        event = Event.objects.current_event()
        if event:
            entries.append(
                NavigationNode(
                    _('Register now for {}').format(event.title),
                    reverse('attendee_registration',
                            kwargs={'event': event.slug}),
                    1, attr={IS_ATTENDEE: False}))
            entries.append(
                NavigationNode(
                    _('Submit session for {}').format(event.title),
                    reverse('create_session',
                            kwargs={'event': event.slug}),
                    2, attr={SUBMISSION_OPEN: True}))
            entries.append(
                NavigationNode(
                    _('Sessions'),
                    event.get_absolute_url(),
                    3, attr={SESSIONS_PUBLISHED: True}))

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

        event = Event.objects.current_event()
        entries.append(
            NavigationNode(
                _('Login'), reverse('auth_login'), 99,
                attr={
                    'visible_for_authenticated': False,
                }))
        profile = NavigationNode(
            _('Profile'), '#', 60,
            attr={
                'icon': 'fa-user',
                'visible_for_anonymous': False,
            })
        entries.append(profile)
        profile.children.append(
            NavigationNode(_('Settings'), reverse('user_profile'), 1))
        if event:
            profile.children.append(
                NavigationNode(
                    _('Checkin QR Code'),
                    reverse('attendee_checkin_qrcode',
                            kwargs={'event': event.slug}),
                    2, attr={CAN_CHECK_IN: True}))
        profile.children.append(
            NavigationNode(
                _('Speaker Profile'),
                reverse('user_speaker_profile'), 3,
                attr={IS_SPEAKER: True}))

        profile.children.append(
            NavigationNode(
                _('Program Committee'),
                reverse('talk_overview'), 4,
                attr={IS_COMMITTEE_MEMBER: True}))
        profile.children.append(
            NavigationNode(_('Logout'), reverse('auth_logout'), 5))
        return entries
