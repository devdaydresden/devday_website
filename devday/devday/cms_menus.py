from menus.base import Menu, NavigationNode
from menus.menu_pool import menu_pool
from django.utils.translation import ugettext_lazy as _


class DevDayMenu(Menu):

    def get_nodes(self, request):
        nodes = [NavigationNode(_('2016'), '/2016/', 1)]
        return nodes


menu_pool.register_menu(DevDayMenu)
