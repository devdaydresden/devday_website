from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from cms.toolbar_pool import toolbar_pool
from devday.utils.devday_toolbar import DevDayToolbarBase
from event.models import Event


@toolbar_pool.register
class DevDayToolbar(DevDayToolbarBase):
    def populate(self):
        super().populate()

        self.add_admin_link_item_alphabetically(_("Send Email"), reverse("send_email"))

        menu = self.add_admin_submenu_alphabetically(
            "reports-menu", _("Reports as CSV")
        )
        self.add_link_item_alphabetically(
            menu, _("Inactive users"), reverse("admin_csv_inactive")
        )
        self.add_link_item_alphabetically(
            menu, _("Users we may contact"), reverse("admin_csv_maycontact")
        )
        self.add_link_item_alphabetically(
            menu, _("Current event attendees"), reverse("admin_csv_attendees")
        )
        self.add_link_item_alphabetically(
            menu,
            _("Current event session summary"),
            reverse("admin_csv_session_summary"),
        )

        current_event = Event.objects.current_event()

        menu = self.add_admin_submenu_alphabetically(
            "stage-menu", _("Actions used on stage during event")
        )
        self.add_link_item_alphabetically(
            menu, _("Raffle"), reverse("raffle", kwargs={"event": current_event.slug})
        )
        self.add_link_item_alphabetically(
            menu,
            _("Event feedback"),
            reverse("event_feedback_summary", kwargs={"event": current_event.slug}),
        )
        self.add_link_item_alphabetically(
            menu,
            _("Session feedback"),
            reverse(
                "attendee_talk_feedback_summary", kwargs={"event": current_event.slug}
            ),
        )
