__kupfer_name__ = _("Media Players")
__kupfer_sources__ = ("MediaPlayerCommandsSource", )
# __kupfer_actions__ = ("Play", )
__kupfer_action_generators__ = ("MediaPlayersGenerator", )
__description__ = _("Control any MPRIS2 Media Player")
__version__ = "0.1"
__author__ = "Jeroen Budts <jeroen@budts.be>"

import dbus

from kupfer import pretty, plugin_support
from kupfer.objects import Source, Leaf, Action
from kupfer.obj.base import ActionGenerator
from kupfer.weaklib import dbus_signal_connect_weakly
from gio.unix import DesktopAppInfo

plugin_support.check_dbus_connection()

class MediaPlayer (object):
    def __init__(self, dbus_obj):
        self._dbus_obj = dbus_obj

    @property
    def root(self):
        return dbus.Interface(self._dbus_obj, dbus_interface='org.mpris.MediaPlayer2')

    @property
    def player(self):
        return dbus.Interface(self._dbus_obj, dbus_interface='org.mpris.MediaPlayer2.Player')

    @property
    def name(self):
        return self.get_root_property('DesktopEntry')

    def _get_property(self, target, property_name):
        properties_manager = dbus.Interface(self._dbus_obj, 'org.freedesktop.DBus.Properties')
        return properties_manager.Get(target, property_name)

    def get_player_property(self, property_name):
        return self._get_property('org.mpris.MediaPlayer2.Player', property_name)

    def get_root_property(self, property_name):
        return self._get_property('org.mpris.MediaPlayer2', property_name)

    @property
    def icon(self):
        # TODO: handle case of absent DesktopEntry (DesktopEntry is optional according to MPRIS2)
        entry = self.get_root_property('DesktopEntry')
        app = DesktopAppInfo(entry + '.desktop')
        return app.get_icon()


class MediaPlayersRegistry (object):
    def __init__(self):
        self.reindex()
        self._setup_monitor()

    def _setup_monitor(self):
        dbus_signal_connect_weakly(dbus.Bus(), 'NameOwnerChanged', self._signal_update,
                                   dbus_interface='org.freedesktop.DBus')

    def _signal_update(self, *args):
        if (len(args) > 0 and args[0].startswith('org.mpris.MediaPlayer2.')):
            self.reindex()

    def reindex(self):
        self.active_players = {}

        bus = dbus.SessionBus()
        dbusObj = bus.get_object('org.freedesktop.DBus', '/')
        for name in dbusObj.ListNames(dbus_interface='org.freedesktop.DBus'):
            if name.startswith('org.mpris.MediaPlayer2.'):
                pretty.print_debug(__name__, "discovered player: " + name)
                dbus_obj = bus.get_object(name, '/org/mpris/MediaPlayer2')
                player = MediaPlayer(dbus_obj)
                self.active_players[player.name] = player
                pretty.print_debug(__name__, "registered player: %s (%s)" % (player.name, player))

    @property
    def players(self):
        for player in self.active_players:
            yield player

    def get_player(self, name):
        return self.active_players[name]


media_players_registry = MediaPlayersRegistry()


class MediaPlayersGenerator (ActionGenerator):
    def get_actions_for_leaf(self, leaf):
        if (isinstance(leaf, MediaPlayerCommandLeaf)):
            return [MediaPlayerAction(player) for player in media_players_registry.players]
        return []


class MediaPlayerAction (Action):
    def __init__(self, player):
        self._player = media_players_registry.get_player(player)
        # TODO: find desktop entry and use name and icon
        Action.__init__(self, player)


    def activate(self, leaf):
        pretty.print_debug(__name__, "activating for " + self._player.name)
        leaf.do_command(self._player)

    def get_gicon(self):
        return self._player.icon

    # TODO: add description?


class MediaPlayerCommandLeaf (Leaf):
    '''a media player leaf'''

    def do_command(self, player):
        raise NotImplementedError('Subclasses should implement this method')


class PlayPause (MediaPlayerCommandLeaf):
    '''play/pause the media player'''
    def __init__(self):
        Leaf.__init__(self, [], _("Play/Pause"))

    def get_icon_name(self):
        return "media-playback-start"

    def get_description(self):
        return _("Resume/Pause playback in the media player")

    def do_command(self, player):
        player.player.PlayPause()


class Play (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Play"))

    def get_icon_name(self):
        return "media-playback-start"

    def get_description(self):
        return _("Start playback in the media player")

    def do_command(self, player):
        player.player.Play()


class Stop (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Stop"))

    def get_icon_name(self):
        return "media-playback-stop"

    def get_description(self):
        return _("Stop playback in the media player")

    def do_command(self, player):
        player.player.Stop()


class Pause (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Pause"))

    def get_icon_name(self):
        return "media-playback-pause"

    def get_description(self):
        return _("Pause playback in the media player")

    def do_command(self, player):
        player.player.Pause()


class Next (MediaPlayerCommandLeaf):
    '''skip to next track in media player'''
    def __init__(self):
        Leaf.__init__(self, [], _("Next"))

    def get_icon_name(self):
        return "media-skip-forward"

    def get_description(self):
        return _("Jump to the next track in the media player")

    def do_command(self, player):
        player.player.Next()


class Previous (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Previous"))

    def get_icon_name(self):
        return "media-skip-backward"

    def get_description(self):
        return _("Jump to the previous track in the media player")

    def do_command(self, player):
        player.player.Previous()


class Quit (MediaPlayerCommandLeaf):
    def __init__(self):
        Leaf.__init__(self, [], _("Quit"))

    def get_icon_name(self):
        return "application-exit"

    def get_description(self):
        return _("Quit the media player")

    def do_command(self, player):
        player.root.Quit()


class MediaPlayersSource (Source):
    '''build a list of currently running media players'''
    def __init__(self):
        Source.__init__(self, _("Media Players"))

    def get_description(self):
        return __description__

    def initialize(self):
        pass

    def _signal_update(self, *args):
        pretty.print_debug('update: ' + ' # '.join(args))


class MediaPlayerCommandsSource (Source):
    '''returns a list of all the commands available for running media players'''
    def __init__(self):
        Source.__init__(self, _("Media Player Commands"))

    def get_description(self):
        return _("Commands that can be executed on a media player, such as play, pause, next.")

    def get_icon_name(self):
        return "applications-multimedia"

    def provides(self):
        yield MediaPlayerCommandLeaf

    def get_items(self):
        yield PlayPause()
        yield Play()
        yield Stop()
        yield Pause()
        yield Next()
        yield Previous()
        yield Quit()