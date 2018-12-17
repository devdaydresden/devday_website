from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from menus.base import Menu, Modifier, NavigationNode
from menus.menu_pool import menu_pool

from talk import COMMITTEE_GROUP
from event.models import Event


CAN_CHECK_IN = 'can_check_in'
CHILDREN = 'children'
EVENT = 'event'
IS_SPEAKER = 'is_speaker'
IS_COMMITTEE_MEMBER = 'is_committee_member'
SUBMISSION_OPEN = 'submission_open'
SESSIONS_PUBLISHED = 'sessions_published'
USER_CAN_REGISTER = 'user_can_register'


@menu_pool.register_menu
class DevDayMenu(Menu):
    """
    Create menu entries for our apps. It appears Django CMS has no easy way to
    add menu items in an ordered way when using multiple register_menu classes.
    It appears they are processed in the order the applications are listed in
    settings.INSTALLED_APPS.  To get the desired order, this class contains
    all the menus across all applications.  Additionally, the modifier below
    will move DevDayMenu entries to the back of the list.
    """

    def get_nodes(self, request):
        entries = []

        event = Event.objects.current_event()
        if event:
            entries.append(
                NavigationNode(
                    _('Register now for {}').format(event.title),
                    reverse('attendee_registration',
                            kwargs={'event': event.slug}),
                    1, attr={USER_CAN_REGISTER: True}))
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

        archive = NavigationNode(_('Archive'), '#', 50, attr={CHILDREN: True})
        events = Event.objects.filter(
            end_time__lt=timezone.now()
            ).exclude(id=Event.objects.current_event_id())
        for e in events.order_by('start_time'):
            archive.children.append(
                NavigationNode(e.title, e.get_absolute_url(),
                               e.id, attr={EVENT: True}))
        entries.append(archive)

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


@menu_pool.register_modifier
class DevDayModifier(Modifier):
    """
    Make sure our DevDayMenu entries are only shown when appropriate.
    Additionally, move our entries to the back of the list, so that CMSMenu
    entries are rendered before ours.
    """

    def user_can_register(self, request, event):
        return (event and event.published
                and event.registration_open
                and (not request.user.is_authenticated
                     or request.user.get_attendee(event) is None))

    def user_can_check_in(self, request, event):
        return (request.user.is_authenticated and event.published
                and request.user.get_attendee(event) is not None)

    def user_is_committee_member(self, request):
        return (request.user.is_authenticated
                and request.user.groups.filter(name=COMMITTEE_GROUP).exists())

    def prune_nodes_with_events(self, nodes, request):
        for node in nodes[:]:
            if EVENT in node.attr:
                e = Event.objects.get(id=node.id)
                if not request.user.is_staff and (
                        not e.published or not e.sessions_published):
                    nodes.remove(node)

    def prune_nodes(self, nodes, attr, fn):
        affected_nodes = list(
            filter(lambda n: attr in n.attr, nodes))
        if affected_nodes:
            b = fn()
            for n in affected_nodes:
                if b != n.attr[attr]:
                    nodes.remove(n)

    def prune_all_nodes(self, nodes, request, event):
        self.prune_nodes(nodes, CAN_CHECK_IN,
                         lambda: self.user_can_check_in(request, event))
        self.prune_nodes(nodes, IS_SPEAKER,
                         lambda: hasattr(request.user, 'speaker'))
        self.prune_nodes(nodes, IS_COMMITTEE_MEMBER,
                         lambda: self.user_is_committee_member(request))
        self.prune_nodes(nodes, USER_CAN_REGISTER,
                         lambda: self.user_can_register(request, event))
        self.prune_nodes(nodes, SUBMISSION_OPEN,
                         lambda: event.submission_open)
        self.prune_nodes(nodes, SESSIONS_PUBLISHED,
                         lambda: (request.user.is_staff
                                  or event.sessions_published))
        self.prune_nodes_with_events(nodes, request)
        for node in nodes:
            if len(node.children):
                self.prune_all_nodes(node.children, request, event)
        for node in nodes[:]:
            if CHILDREN in node.attr and len(node.children) == 0:
                nodes.remove(node)

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if not post_cut:
            event = Event.objects.current_event()
            self.prune_all_nodes(nodes, request, event)
            # move our entries to the back of the list
            ours = []
            others = []
            for n in nodes:
                if n.namespace == 'DevDayMenu':
                    ours.append(n)
                else:
                    others.append(n)
            nodes = others + ours
        return nodes
