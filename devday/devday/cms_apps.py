from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _


@apphook_pool.register
class DevDayApphook(CMSApp):
    name = _("Dev Day")

    def get_urls(self, page=None, language=None, **kwargs):
        return []
