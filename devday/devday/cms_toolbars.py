from cms.toolbar_pool import toolbar_pool
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from devday.utils.devday_toolbar import DevDayToolbarBase


@toolbar_pool.register
class DevDayToolbar(DevDayToolbarBase):
    def populate(self):
        super().populate()

        self.add_admin_sideframe_item_alphabetically(
            _('Send Email'), reverse('send_email'))

        menu = self.add_admin_submenu_alphabetically(
            'reports-menu', _('Reports as CSV'))
        self.add_link_item_alphabetically(
            menu, _('Inactive users'), reverse('admin_csv_inactive'))
        self.add_link_item_alphabetically(
            menu, _('Users we may contact'), reverse('admin_csv_maycontact'))
        self.add_link_item_alphabetically(
            menu, _('Current event attendees'),
            reverse('admin_csv_attendees'))
