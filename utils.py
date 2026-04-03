__author__ = 'stas Zytkiewicz stas@childsplay.mobi'

# Copyright (c) 2022 Stas Zytkiewicz <stas@childsplay.mobi>
# Copyright (c) 2022 BTP <info@btp.nl>
#
#           NMKivy
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License
# as published by the Free Software Foundation.  A copy of this license should
# be included in the file GPL-3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
import builtins
import gettext
import os
import subprocess

import locale
import logging
import time
import urllib3
import nmcli
from nmcli import NotExistException

from SPLogging import DuplicateFilter

nmcli.disable_use_sudo()

LOCALEDIR = 'locale'

# These will be changed by a call to set_locale in main-nm.py
LANG = 'en'
LOCALE_RTL = None
PROVISIONER =  "https://provisioner.braintrainerplus.com.au"

IP_NL = "https://provisioner.btp.nl"
IP_AU = "https://provisioner.braintrainerplus.com.au"
IP_ES = "https://provisioner.braintrainerplus.es"
IP_BE = "https://provisioner.braintrainerplus.be"
IP_NZ = "https://provisioner.braintrainerplus.co.nz"

module_logger = logging.getLogger('sp.utils')
module_logger.addFilter(DuplicateFilter()) # this will filter repeated messages from check_provisioner

def start_network():
    """
    Switch on networking including wifi radio. It will check if the network and wifi is
    switched on
    :return: True on success, None on failure
    """
    nmcli.networking.on()
    result = nmcli.networking()
    time.sleep(1)
    if result.name != 'FULL':
        module_logger.error("Failed to bring up networking")
        return None
    nmcli.radio.wifi_on()
    #time.sleep(1)
    # This seems to fail everytime, so we don't check it
    # result = nmcli.radio().to_json()
    # if not result['wifi']:
    #     module_logger.error("Failed to bring up wifi radio")
    #     return None
    module_logger.info("Networking and wifi radio up")
    return True


def scan_wifi():
    """
    Scan for available wifi ssid. It will remove access points without ssid
    :return: json with access points data, None on failure
    """
    result = nmcli.device.wifi() or None
    if result:
        result = [item.to_json() for item in result]
        result = [item for item in result if item['ssid'] != '']
    module_logger.debug(f"scan_wifi found: {result}")
    return result


def scan_eth():
    """Get available """
    result = nmcli.device() or None
    if result:
        result = [item.to_json() for item in result]
        result = [item for item in result if item['device_type'] == 'ethernet']
    module_logger.debug(f"scan_eth found: {result}")
    return result


def connect_wifi(ssid: str, password: str = None):
    """
    Will connect to the ssid. It expects the password to be set already.
    If not, you need to add the connection first by calling 'add_connection'
    :return: 1 on success, 0 on failure, -1 on unknown connection, -2 on password failure.
    """
    if password:
        # we assume a new connection on wifi
        try:
            nmcli.device.wifi_connect(ssid, password)
        except Exception as e:
            module_logger.error(f"Failed to connect to wifi: {e}")
            return -2
        else:
            return 1
    else:
        # we assume an eth when no password is given
        try:
            result = nmcli.connection.up(ssid)
        except NotExistException as e:
            return -1
        except nmcli.ConnectionActivateFailedException as e:
            module_logger.error(f"Could be wrong password for {ssid}")
            return 2
        except Exception as e:
            module_logger.error(f"Failed to connect ssid {ssid}: {e}")
            return 0
        else:
            return 1

def disconnect_connection(connection):
    """
    Disconnect a connection
    :param connection: the connection name
    :return: True on success, False on failure
    """
    try:
        nmcli.connection.down(connection)
    except Exception as e:
        module_logger.error(f"Failed to disconnect connection {connection}: {e}")
        return False
    else:
        return True

def get_current_connections():
    """
    get the current connections. We only want to include wifi and eth connections.
    Those have nm id 802-11-wireless and 802-3-ethernet
    :return: a list with tuples with the name and ip from each connection on success, empty list when no connections
    are available.
    """
    connections = []
    result = nmcli.connection()
    for con in result:
        module_logger.debug(f"get_current_connections: {con}")
        try:
            data = nmcli.connection.show(con.name)
        except Exception as e:
            module_logger.error(f"get_current_connections failed to get data for {con.name!r}: {e}")
            continue
        #module_logger.debug(f"get_current_connections con data: {data}")
        if data['connection.type'] in ['802-11-wireless', '802-3-ethernet'] and \
                'IP4.ADDRESS[1]' in data.keys() or 'IP6.ADDRESS[1]' in data.keys():
            connections.append((data['connection.id'], data['IP4.ADDRESS[1]'].split('/')[0]))
    return connections

def check_provisioner():
    http = urllib3.PoolManager()
    try:
        request = http.request('GET', PROVISIONER)
    except Exception as info:
        module_logger.error(f"check_provisioner {PROVISIONER} failed: {info}")
    else:
        if request.status == 200:
            module_logger.info(f"check_provisioner: {PROVISIONER} is available")
            return True

def reset_connection(ssid):
    nmcli.connection.delete(ssid)

def add_connection(data: dict):
    """
    Add a connection
    :param data:
    :return:
    """
    pass

def delete_all_connections(*args):
    """
    Forget all connections except ethernet
    :return:
    """
    # we remove the system connections
    module_logger.debug("delete_all_connections called")
    cmd = 'sudo /data/tools/remove_nm_connections'
    try:
        child = subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as info:
        module_logger.error(f"delete_all_connections: {info}")
        return False
    else:
        if child != 0:
            module_logger.error("delete_all_connections: Failed to remove connections")
            return False
        else:
            return True


def _set_provisioner(provisioner_lang):
    global PROVISIONER
    lang = provisioner_lang.split('.')[0]
    if lang == 'nl_NL':
        PROVISIONER = IP_NL
    elif lang == 'en_AU':
        PROVISIONER = IP_AU
    elif lang == 'es_ES':
        PROVISIONER = IP_ES
    elif lang == 'nl_BE':
        PROVISIONER = IP_BE
    elif lang == 'en_NZ':
        PROVISIONER = IP_NZ
    else:
        PROVISIONER = IP_AU

def set_locale(lang=None):
    """Used by the core to set the locale.
    """
    module_logger.debug(f"set_locale called with {lang}")
    global LOCALE_RTL, LANG, PROVISIONER
    provisioner_lang = LANG
    txt = ""
    try:
        if not lang or lang == 'system':
            try:
                lang, enc = locale.getdefaultlocale()
                lang = "%s.%s" % (lang, enc.upper())
            except ValueError as info:
                module_logger.error(f"set_locale: {info}")
                lang = 'en_US.utf8'
        languages = [lang]
        lang, enc = lang.split('.')
        lang = f"{lang}.{enc.lower()}"
        locale.setlocale(locale.LC_ALL, (lang.split('.')))
        provisioner_lang = lang
        module_logger.info(f"set_locale: Setting nmkivy locale to '{lang}' modir: {LOCALEDIR}")
        gettext.textdomain('nmkivy')
        lang_trans = gettext.translation('nmkivy',
                                         localedir=LOCALEDIR,
                                         languages=languages)
        gettext.install('nmkivy', LOCALEDIR)
        os.environ['LANG'] = lang
        builtins.__dict__['_'] = lang_trans.gettext
    except Exception as info:
        txt = f"Cannot set language to '{lang}' \n switching to English"
        module_logger.error(f"set_locale: {info}, {txt}")
        builtins.__dict__['_'] = lambda x: x
        lang = 'en_US.utf8'
    else:
        lang = lang.split('@')[0]

    # This is to signal that we running under a RTL locale like Hebrew or Arabic
    # Only Hebrew and Arabic is supported until now
    if lang[:2] in ['he', 'ar']:
        LOCALE_RTL = True
    else:
        LOCALE_RTL = False
    LANG = lang
    module_logger.info("set_locale: Locale set to %s, RTL set to %s" % (LANG, LOCALE_RTL))
    _set_provisioner(provisioner_lang)
    nmcli.set_lang(lang)
    return lang, LOCALE_RTL
