from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


@toolbar_pool.register
class DevDayToolbar(CMSToolbar):
    def populate(self):
        menu = self.toolbar.get_or_create_menu('devday', _('Dev Day'))
        url = reverse('send_email')
        menu.add_link_item(_('Send Email'), url=url)
        url = reverse('admin_csv_inactive')
        menu.add_link_item(_('Inactive users'), url=url)
        url = reverse('admin_csv_maycontact')
        menu.add_link_item(_('Users we may contact'), url=url)
        url = reverse('admin_csv_attendees')
        menu.add_link_item(_("Current event attendees"), url=url)
