# Copyright (C) 2024  Stas@childsplay.mobi
# Copyright (C) 2024  BraintrainerPlus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


__author__ = 'stas Zytkiewicz stas@childsplay.mobi'

import os
# Will setup logging
import sys

import SPLogging
import utils

SPLogging.set_level('debug')
SPLogging.start()

import logging
module_logger = logging.getLogger("sp.main")

#### Applies BTP specific styling for kivy widgets ######
from os import environ

from Style import StyleBase

environ['KIVY_DATA_DIR'] = 'patches/data'
from kivy.resources import resource_add_path
resource_add_path('patches')
##########################################################

from utils import *
set_locale()

from kivy.config import Config
# print("**** enable the inspector ****")
# Config.set('modules', 'inspector', 1)
print(environ.keys())
if 'DEBUG' not in environ.keys():
    Config.set('graphics', 'fullscreen', 'auto')
else:
    Config.set('modules', 'inspector', 1)

from functools import partial

import kivy
kivy.require('2.0.0')
module_logger.info(f"Using kivy from {kivy}")

from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App

base = os.path.dirname(os.path.abspath(__file__))
Builder.load_file(os.path.join(base, 'main-nm.kv'))


updater_text = _("""Your about to start the updater which will update this system.
Be aware that this can take between 15 minutes and one hour depending on the size of the update.

** The update can not be interrupted! ** 

Do you want to start updating this system?""")

class MyLabel(Label):
    pass

class MyToggle(ToggleButton):
    text = StringProperty("Connect")
    connected_state = False

class BusyBody(FloatLayout):
    angle = NumericProperty(0)
    image_source = 'buttons/busybody.png'
    stop_me = True

    def __init__(self, **kwargs):
        super(BusyBody, self).__init__(**kwargs)
        self.anim = Animation(angle=360, duration=2)
        self.anim += Animation(angle=360, duration=2)

    def on_angle(self, item, angle):
        if angle == 360:
            item.angle = 0

    def start(self, *args):
        print("busybody started")
        self.anim.repeat = True
        self.anim.start(self)

    def stop(self, *args):
        self.anim.repeat = False
        self.anim.stop(self)

class _InputContent(BoxLayout):
    """
    Build by kv
    """

    input = ObjectProperty()
    text_ok = StringProperty(_("Connect"))
    text_exit = StringProperty(_("Exit"))
    text_pass = StringProperty(_("Wifi password"))
    text_show = StringProperty(_("Show password"))

    def __init__(self, obs, parent=None, **kwargs):
        super(_InputContent, self).__init__(**kwargs)
        self.obs = obs
        self.my_parent = parent

    def on_start_button_clicked(self):
        self.my_parent.dismiss()
        Clock.schedule_once(partial(self.obs, self.ids.input.text))

    def on_close_button_clicked(self):
        self.my_parent.dismiss()
        self.obs('')

class InputDialog(Popup):
    def __init__(self, title=_('Please give a password'), lbltext=_('Wifi Password'), obs=None, **kwargs):
        """Extends the kivy popup dialog with a custom content object.
        title and text must be strings.
        obs is a function that will be called when the user hits the 'Start' button and must except
        a string or none. The string will be the text entered or None if the close button is used.
        """
        super(InputDialog, self).__init__(title=title, size_hint=(0.9, 0.4), auto_dismiss=False)
        self.auto_dismiss = False
        self.pos_hint = {'center_y': 0.5}
        self.content = _InputContent(obs, parent=self, **kwargs)
        self.border = (74, 32, 74, 32)


    def on_dismiss(self):
        Window.release_all_keyboards()

    def get_text(self):
        return self.content.input.text

class _YesNoDialogContent(BoxLayout):
    """Object build by kv."""
    text = StringProperty('')
    text_yes = StringProperty(_("Yes"))
    text_no = StringProperty(_("No"))

    def __init__(self, text, parent):
        BoxLayout.__init__(self)
        self.my_parent = parent
        self.text = text
        self.fontsize = '18dp'

    def on_no_button_clicked(self):
        self.my_parent.on_no_button_clicked()

    def on_yes_button_clicked(self):
        self.my_parent.on_yes_button_clicked()


class YesNoDialog(Popup):
    def __init__(self, title, text, cbf, cbf_no=None, size_hint=(0.8, 0.8), content=None, **kwargs):
        """Extends the kivy popup dialog with a custom content object.
        title and text must be strings.
        cbf is a function that will be called when the user hits the 'Yes' button.
        """

        if not content:
            text = StyleBase.texttags % text
            content = _YesNoDialogContent(text, self)

        Popup.__init__(self, title=title, title_size=StyleBase.titlesize, size_hint=size_hint,
                       content=content, auto_dismiss=False)
        self.cbf = cbf
        self.cbf_no = cbf_no
        self.border = (74, 32, 74, 32)
        self.separator_color = StyleBase.separator_color

    def on_no_button_clicked(self):
        self.dismiss()
        if self.cbf_no:
            self.cbf_no()

    def on_yes_button_clicked(self, *args):
        self.dismiss()
        if self.cbf:
            self.cbf()


class NMDialog(BoxLayout):
    """
    Build by kv
    """

    text_scan = StringProperty(_("Scan"))
    text_close = StringProperty(_("Exit"))
    text_update = StringProperty(_("Start Update"))

    anim = None

    def __init__(self, **kwargs):
        super(NMDialog, self).__init__()
        self.pos_hint = {'center_y': 0.5}
        self.toggles = {}
        self.pb_ev = None
        self.logger = logging.getLogger('sp.NMDialog')


    def _blink_text(self):
        self.anim = Animation(opacity=1, duration=0.1) + Animation(opacity=1, duration=3)
        self.anim += Animation(opacity=0, duration=0.1) + Animation(opacity=0, duration=0.5)
        self.anim.repeat = True
        self.anim.start(self.ids.status_label)

    def start_progressbar(self):
        self.stop_progressbar()
        self.pb_ev = Clock.schedule_interval(self._start_progressbar, 1/30)

    def _start_progressbar(self, *args):
        progress_bar = self.ids.prog_b
        current = progress_bar.value
        if current >= progress_bar.max:
            current = progress_bar.min
        else:
            current += 1
        progress_bar.value = current
        return True

    def stop_progressbar(self, *args):
        if self.pb_ev:
            self.pb_ev.cancel()
        self.ids.prog_b.value = 0

    def register_observer(self, obs):
        self.observer = obs
        Clock.schedule_once(self.observer.start, 0.2)

    def on_connect_toggle_button_clicked(self, toggle):
        self.display_message(_(f"Connecting to {toggle.ssid}, please wait..."))
        Clock.schedule_once(partial(self.observer.on_connect_button_clicked, (toggle.ssid, toggle)))

    def on_scan_button_clicked(self, *args):
        """ Called from the kv gui and controller"""
        self.display_message(_("Scanning, please wait..."))
        # self.start_progressbar()
        Clock.schedule_once(self.observer.on_scan_button_clicked)

    def on_forget_button_clicked(self, *args):
        self.display_message(_("Forgetting all connections..."))
        YesNoDialog(_("Forget all connections?"), _("Are you sure you want to forget all connections?"),
                     self.observer.on_forget_button_clicked).open()

    def display_message(self, txt, blink=False):
        if blink and not self.anim:
            self._blink_text()
        elif self.anim and not blink:
            self.anim.stop()
            self.anim = None
        self.ids.status_label.text = txt

    def fill_wifi_box(self, items):
        layout = GridLayout(cols=2, spacing=10, size_hint_y=None)
        # Make sure the height is such that there is something to scroll.
        layout.bind(minimum_height=layout.setter('height'))
        for item in items:
            self.logger.debug(f"fill_wifi_box: {item}")
            tb = MyToggle(size_hint=(0.2, None), height=40)
            tb.ssid = item['ssid']
            if item['in_use']:
                tb.state = 'down'
                tb.connected_state = True
            layout.add_widget(tb)
            self.toggles[item['ssid']] = tb
            txt = f"WIFI: {item['ssid']:20} - Signal: {item['signal']:4} - {item['security']}"
            lbl = MyLabel(text=txt, font_size='15dp', font_name='RobotoMono-Regular')
            layout.add_widget(lbl)

        self.ids.wifibox.clear_widgets()

        self.ids.wifibox.add_widget(layout)
        self.display_message(_("Scanning done."))

    def fill_eth_box(self, items):
        self.ids.ethbox.clear_widgets()
        for item in items:
            self.logger.debug(f"fill_eth_box: {item}")
            tb = MyToggle(size_hint=(0.2, None), height=40, group='eth')
            tb.ssid = item['connection']
            if item['state'] == 'connected':
                tb.state = 'down'
                tb.connected_state = True
            self.ids.ethbox.add_widget(tb)
            self.toggles[item['connection']] = tb
            txt = f"ETH: {item['connection']} - State: {item['state']}"
            lbl = MyLabel(text=txt, font_size='15dp', )
            self.ids.ethbox.add_widget(lbl)


class Controller:
    """
    Class to control the gui and backend
    """

    def __init__(self, gui):
        self.Gui = gui
        self.input_dlg = None
        self.logger = logging.getLogger('sp.Controller')

    def _get_wifi_pass(self, ssid, pas, *args):
        """observer for the InputDialog"""
        #print(f"_get_wifi_pass {ssid} {pas}")
        if not pas:
            # probabaly hit the exit button
            return

        self.Gui.display_message(_(f"Start Connecting to {ssid}..."))
        # self.Gui.start_progressbar()
        result = connect_wifi(ssid, pas)
        # self.Gui.stop_progressbar()
        if not result:
            self.Gui.display_message(_(f"Failed to connect to {ssid}"))
        elif result == 1:
            self.Gui.display_message(_(f"Connected to {ssid}"))
        else:
            self.Gui.display_message(_(f"Failed to connect to {ssid}, check your password."))

    def _check_for_connected(self, *args):
        """Called by a Clock interval, make sure we don't throw an exception """
        # self.Gui.start_progressbar()
        try:
            cons = get_current_connections()
        except Exception as e:
            self.logger.error(f"failed to check for connections: {e}")
            cons = []
            # self.Gui.stop_progressbar()
            return

        # we cycle through all the toggles to set them as disconnected
        # as when we have a connection we set that toggle as connected
        txt = ''
        for ssid, tb in self.Gui.toggles.items():
            tb.state = 'normal' # text will change, see kv
            tb.connected_state = False
        if cons:
            for con in cons:
                self.logger.debug(f"using connection: {con}")
                if not len(con) >= 2:
                    continue
                txt = txt + _(f"Connected {con[0]} to {con[1]}\n")
                ssid = con[0]
                if ssid not in self.Gui.toggles.keys():
                    self.logger.info(f"Could not find {ssid} in toggles, moving on")
                    continue
                self.Gui.toggles[con[0]].state = 'down'
                self.Gui.toggles[con[0]].connected_state = True

            if not check_provisioner():
                self.logger.warning("Cannot connect to the BTP+ server")
                text = _("Cannot connect to the BTP+ server. Please use another connection or contact your IT department.")
                self.Gui.display_message(f"[b][color=#e81f1f]{text}[/color][/b]", blink=True)
                self.Gui.ids.update_button.disabled = True
            else:
                self.logger.info("BTP+ server is available")
                self.Gui.display_message(_("The BTP+ server is available. You can update this machine."),
                                         blink=False)
                self.Gui.ids.update_button.disabled = False
        else:
            self.logger.warning("No connections found")
            txt = 'Not connected'
            self.Gui.ids.update_button.disabled = True
        # self.Gui.stop_progressbar()
        self.Gui.ids.connect_label.text = txt.rstrip('\n')

    def _scan_eth(self, *args):
        # self.Gui.start_progressbar()
        items = scan_eth()
        # self.Gui.stop_progressbar()
        if not items:
            self.Gui.display_message(_("No wired device found"))
            return True
        self.Gui.fill_eth_box(items)
        return True

    def _scan_wifi(self, *args):
        # self.Gui.start_progressbar()
        items = scan_wifi()
        # self.Gui.stop_progressbar()
        if not items:
            self.Gui.display_message(_("No wifi access points found"))
            return True
        self.Gui.fill_wifi_box(items)
        return True

    def start(self, *args):
        """Called from the gui after we registered as a observer"""
        self.logger.info("Controller starting...")
        self._start()

    def _start(self, *args):
        # First we start networking and wifi radio
        #cl_ev = Clock.schedule_once(self.Gui.ids.busybody.start)
        # self.Gui.start_progressbar()
        if not start_network():
            self.Gui.display_message(_("Failed to start network and/or wifi radio\nMake sure the wifi is enabled."))
            self.Gui.display_message(_("Start network scan again after 3 seconds, please wait..."))
            Clock.schedule_once(self._scan_wifi, 3)
            Clock.schedule_once(self._scan_eth, 3)
            Clock.schedule_once(self._check_for_connected, 4)
        else:
            self.Gui.display_message(_("Start network scanning, please wait..."))
            self._scan_wifi()
            self._scan_eth()
            self._check_for_connected()

        # We start a clock interval to display the current connection
        #Clock.schedule_interval(self._check_for_connected, 5)
        Clock.schedule_once(self._check_for_connected, 4)

    ## Toggle buttons callback
    def on_connect_button_clicked(self, data, *args):
        """Called when a toggle button is clicked"""
        ssid, obj = data
        self.logger.info(f"on_connect_button_clicked called with: {ssid}")
        print(f"obj.connected_state: {obj.connected_state}")
        if obj.connected_state:
            module_logger.debug(f"Disconnecting {ssid}")
            self.Gui.display_message(_(f"Disconnecting from {ssid}, please wait..."))
            if not disconnect_connection(ssid):
                self.Gui.display_message(_(f"Failed to disconnect from {ssid}"))
            else:
                obj.state = 'normal'
                obj.connected_state = False
                self.Gui.display_message(_(f"Disconnected from {ssid}"))
                Clock.schedule_once(self._check_for_connected, 1)
            return

        self.Gui.display_message(_(f"Start connecting to {ssid}, please wait..."))

        # self.Gui.start_progressbar()
        result = connect_wifi(ssid)
        # self.Gui.stop_progressbar()
        if not result:
            self.Gui.display_message(_(f"Failed to connect to {ssid}"))
            obj.state = 'normal'
        elif result == 2:
            self.Gui.display_message(_(f"Failed to connect to {ssid}, wrong password?"))
            reset_connection(ssid)
        elif result == -1:
            # Unknown connection, needs a password (probably)
            InputDialog(obs=partial(self._get_wifi_pass, ssid)).open()
        else:
            obj.state = 'down'
            obj.connected_state = True
            self.Gui.display_message(_(f"Connected to {ssid}"))
            self._check_for_connected()

    ## Bottom buttons callbacks
    def on_scan_button_clicked(self, *args):
        """ Called from the gui"""
        Clock.schedule_once(self._scan_wifi)
        Clock.schedule_once(self._scan_eth)
        Clock.schedule_once(self._check_for_connected, 1)

    def on_update_button_clicked(self):
        """ Called from the kv"""
        self.logger.info(f"on_update_button_clicked")

        def cbf():
            print("cbf called")
            self.on_close_button_clicked()
            if 'DEBUG' in os.environ.keys():
                print("Running in debug, fake starting updater")
                sys.exit(0)
            else:
                os.system('sudo /usr/local/bin/start_updater &')

        dlg = YesNoDialog("Start Update?", updater_text, cbf=cbf)
        dlg.open()


    def on_close_button_clicked(self):
        """ Called from the kv"""
        self.logger.info(f"on_close_button_clicked")
        # In case we have a onscreen keyboard
        Window.release_all_keyboards()
        App.get_running_app().stop()
        os.system('/usr/local/bin/start_gamesmenu_classic')

    def on_forget_button_clicked(self):
        """ Called from the kv"""
        self.logger.info(f"on_forget_button_clicked")
        result = delete_all_connections()
        if not result:
            self.Gui.display_message(_("Failed to forget all connections"))
        else:
            self.Gui.display_message(_("All connections forgotten"))
            Clock.schedule_once(self._check_for_connected, 1)


if __name__ == "__main__":

    class MyApp(App):
        def build(self):
            dlg = NMDialog()
            C = Controller(dlg)
            dlg.register_observer(C)
            return dlg

    MyApp().run()
