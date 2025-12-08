import nmcli
nmcli.disable_use_sudo()

import SPLogging
SPLogging.set_level('debug')
SPLogging.start()

# try:
#     print(nmcli.connection())
#     print(nmcli.device())
#     print(nmcli.device.wifi())
#     print(nmcli.general())
#
#     nmcli.device.wifi_connect('AP1', 'passphrase')
#     nmcli.connection.modify('AP1', {
#             'ipv4.addresses': '192.168.1.1/24',
#             'ipv4.gateway': '192.168.1.255',
#             'ipv4.method': 'manual'
#         })
#     nmcli.connection.down('AP1')
#     nmcli.connection.up('AP1')
#     nmcli.connection.delete('AP1')
# except Exception as e:
#     print(e)

# print("\n========= nmcli.device ================\n" )
# result = nmcli.device()
# print(result)
#
# print("\n========= nmcli.device.show_all ================\n" )
# result = nmcli.device.show_all()
# for item in result:
#     print(item)
#
# print("\n=========== nmcli.device.wifi ================\n")
# result = nmcli.device.wifi()
# for item in result:
#     print(item)

print("\n=========== stuff ================\n")
import utils
utils.delete_all_connections()

# result = nmcli.connection.up('TuxhomeAsusGuest1')
# print(f"result wifi_connect: {result}")
#nmcli.connection.down('TuxhomeAsusGuest1')