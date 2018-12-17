import locale

from cms.toolbar import items
from cms.toolbar_base import CMSToolbar
from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK


class DevDayToolbarBase(CMSToolbar):
    DEVDAY_BREAK = 'devday-break'

    def position_in_admin_section(self, name):
        parent = self.admin_menu
        first = parent.find_first(
            items.Break, identifier=ADMINISTRATION_BREAK) + 1
        last = parent.find_first(
            items.Break, identifier=self.DEVDAY_BREAK)
        if not last:
            last_item = parent.add_break(self.DEVDAY_BREAK, position=first)
            last = items.ItemSearchResult(
                last_item, parent._item_position(last_item))
        lname = locale.strxfrm(name.lower())
        for item in parent.items[first.index:last.index]:
            if locale.strcoll(
                    locale.strxfrm(str(item.name).lower()), lname) > 0:
                position = items.ItemSearchResult(
                    item, parent._item_position(item))
                break
        else:
            position = last
        return position.index

    def add_admin_link_item_alphabetically(self, name, url):
        position = self.position_in_admin_section(name)
        item = self.admin_menu.add_link_item(name, url=url, position=position)
        return item

    def add_admin_submenu_alphabetically(self, label, name):
        position = self.position_in_admin_section(name)
        menu = self.admin_menu.get_or_create_menu(
            label, name, position=position)
        return menu

    def add_link_item_alphabetically(self, menu, name, url):
        position = menu.get_alphabetical_insert_position(
            name, items.LinkItem)
        item = menu.add_link_item(name, url=url, position=position)
        return item

    def populate(self):
        self.admin_menu = self.toolbar.get_menu(ADMIN_MENU_IDENTIFIER)
