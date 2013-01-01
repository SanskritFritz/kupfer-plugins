"""
A plugin to control Hotot
"""

__kupfer_name__ = _("Hotot")
__kupfer_actions__ = ("SendUpdate", "Show", "Hide", "Quit", )
__description__ = _("Control Hotot")
__version__ = "1.0"
__author__ = "Jeroen Budts <jeroen@budts.be>"

import dbus

from kupfer.objects import Action, TextLeaf, AppLeaf
from kupfer import pretty, plugin_support

plugin_support.check_dbus_connection()

def get_hotot():
    try:
        bus = dbus.SessionBus()
        dbusObj = bus.get_object('org.hotot.service', '/org/hotot/service')
        return dbus.Interface(dbusObj, dbus_interface='org.hotot.service')
    except dbus.exceptions.DBusException, err:
        pretty.print_debug(err)
    return None

class SendUpdate (Action):
    ''' Create a Tweet with Hotot '''
    def __init__(self):
        Action.__init__(self, _("Send Update"))

    def activate(self, leaf):
        pretty.print_debug(__name__, leaf.object)
        text = leaf.object.replace('"', '\\"')
        pretty.print_debug(__name__, "SendUpdate: "+text)
        get_hotot().update_status(text)

    def item_types(self):
        yield TextLeaf

    def get_description(self):
        return _("Send an update to Twitter with Hotot")

    def get_icon_name(self):
        return 'hotot'

    def valid_for_item(self, item):
        return get_hotot() != None

class HototAction (Action):
    def __init__(self, action, func):
        self.action = action
        self.func = func
        Action.__init__(self, _(action))

    def get_description(self):
        return _(self.action + ' the running Hotot instance')

    def activate(self, leaf):
        self.func(get_hotot())

    def item_types(self):
        yield AppLeaf

    def valid_for_item(self, item):
        return item.name == 'Hotot' and get_hotot() != None

class Show (HototAction):
    def __init__(self):
        def show_action(hotot):
            hotot.show()
        HototAction.__init__(self, 'Show', show_action)
    def get_icon_name(self):
        return "go-jump"

class Hide (HototAction):
    def __init__(self):
        def hide_action(hotot):
            hotot.hide()
        HototAction.__init__(self, 'Hide', hide_action)
    def get_icon_name(self):
        return "window-close"

class Quit (HototAction):
    def __init__(self):
        def quit_action(hotot):
            hotot.quit()
        HototAction.__init__(self, 'Quit', quit_action)
    def get_icon_name(self):
        return "application-exit"
