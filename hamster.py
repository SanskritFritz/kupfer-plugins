__kupfer_name__ = _("Hamster")
__description__ = _("Control the Hamster time tracker")
__author__ = "Jeroen Budts"
__kupfer_actions__ = ("Toggle",)
__kupfer_sources__ = ("HamsterSource",)

import dbus

from kupfer.objects import Action, AppLeaf, Source, Leaf, RunnableLeaf, SourceLeaf
from kupfer import pretty, plugin_support, icons
from kupfer.obj.apps import AppLeafContentMixin
import time

HAMSTER_APPNAMES = ("hamster-indicator", "hamster-time-tracker", )

plugin_support.check_dbus_connection()

def get_hamster():
    try:
        bus = dbus.SessionBus()
        dbusObj = bus.get_object('org.gnome.Hamster', '/org/gnome/Hamster')
        return dbus.Interface(dbusObj, dbus_interface='org.gnome.Hamster')
    except dbus.exceptions.DBusException, err:
        pretty.print_debug(err)
    return None


class HamsterAction (Action):
    pass


class Toggle (HamsterAction):
    def __init__(self):
        HamsterAction.__init__(self, _("Open / Close"))

    def item_types(self):
        yield AppLeaf

    def valid_for_item(self, item):
        return item.get_id() in HAMSTER_APPNAMES and get_hamster() != None

    def activate(self, leaf):
        get_hamster().Toggle()

    def get_description(self):
        return _("Open or close Hamster")

    def get_icon_name(self):
        return 'go-jump'


class StartActivity (HamsterAction):
    def __init__(self):
        HamsterAction.__init__(self, _("Start activity"))

    def item_types(self):
        #TODO: textleaf
        yield ActivityLeaf

    def activate(self, leaf):
        get_hamster().AddFact(leaf.object, time.time() - time.timezone, 0, False)

    def get_description(self):
        return _("Start tracking the activity in Hamster")


class StopTrackingLeaf (RunnableLeaf):
    #TODO: this only makes sense when an activity is being tracked
    def __init__(self):
        RunnableLeaf.__init__(self, name=_("Stop tracking"))

    def get_description(self):
        return _("Stop tracking the current activity")

    def get_gicon(self):
        return icons.ComposedIconSmall("hamster-applet", self.get_icon_name())

    def get_icon_name(self):
        return "process-stop"

    def run(self):
        get_hamster().StopTracking(time.time() - time.timezone)


class ActivityLeaf (Leaf):
    def __init__(self, activity):
        Leaf.__init__(self, activity, activity)

    def get_actions(self):
        return (StartActivity(), )


class HamsterSource (AppLeafContentMixin, Source):
    appleaf_content_id = HAMSTER_APPNAMES

    def __init__(self):
        Source.__init__(self, _("Hamster"))

    def provides(self):
        yield StopTrackingLeaf
        yield SourceLeaf

    def get_items(self):
        yield StopTrackingLeaf()
        activities = ActivitiesSource()
        yield SourceLeaf(activities)


class ActivitiesSource (Source):
    # TODO: option to export activities to toplevel, similar to Rhytmbox
    def __init__(self):
        Source.__init__(self, _("Hamster activities"))

    def provides(self):
        yield ActivityLeaf

    def get_items(self):
        for act in get_hamster().GetActivities(''):
            activity = act[0]
            if act[1]:
                activity += '@' + act[1]
            yield ActivityLeaf(activity)
