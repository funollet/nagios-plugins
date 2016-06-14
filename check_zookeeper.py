#!/usr/bin/env python
# check_zookeeper.py
#
# Nagios plugin; checks a server's status in a Zookeeper cluster.


from telnetlib import Telnet
import socket
from pynag.Plugins import PluginHelper, ok, warning, critical, unknown

TELNET_TIMEOUT = 3


class ZkClient:
    def __init__(self, host, port, timeout=TELNET_TIMEOUT):
        """Connect to zookeper's client.
        """
        self.host = host
        self.port = port
        self.timeout = timeout


    def cmd(self, word):
        """Connect and send a 4letter command to Zookeeper.
        """
        # Zookeeper closes the socket after every command, so we must reconnect every time.
        tn = Telnet(self.host, self.port, self.timeout)
        tn.write('{}\n'.format(word))
        return tn.read_all()



if __name__ == '__main__':
    plugin = PluginHelper()
    plugin.parser.add_option("-H","--hostname", help="Zookeeper's host", default='127.0.0.1')
    plugin.parser.add_option("-p","--port", help="Zookeeper's port", default='2181')
    plugin.parse_arguments()

    try:
        zk = ZkClient(plugin.options.hostname, plugin.options.port)
    except socket.error:
        plugin.status(critical)
        plugin.add_summary("Can't connect to {}:{}".format(plugin.options.hostname, plugin.options.port))
        plugin.exit()

    try:
        if zk.cmd('ruok') != 'imok':
            plugin.status(critical)
            plugin.add_summary("Command 'ruok' failed")
            plugin.exit()
    except socket.error, socket.timeout:
        plugin.status(critical)
        plugin.add_summary("Can't connect to {}:{}".format(plugin.options.hostname, plugin.options.port))
        plugin.exit()

    try:
        if zk.cmd('isro') != 'rw':
            plugin.status(critical)
            plugin.add_summary("Zookeeper is not read-write (network partition? quorum?)")
            plugin.exit()
    except socket.error, socket.timeout:
        plugin.status(critical)
        plugin.add_summary("Can't connect to {}:{}".format(plugin.options.hostname, plugin.options.port))
        plugin.exit()

    # Get Zookeeper's status.
    txt = zk.cmd('mntr')
    # Parse lines of keys/values into a dictionary.
    mntr = dict( l.split('\t') for l in txt.strip().split('\n') if '\t' in l )

    # Run checks.
    state = mntr.get('zk_server_state', None)

    if state in ['observer', 'standalone']:
        plugin.status(critical)
        plugin.add_summary("zk_server_state: {}".format(state))
    elif state in ['leader_election']:
        plugin.status(warning)
        plugin.add_summary("zk_server_state: {}".format(state))
    elif state not in ['leader', 'follower']:
        plugin.status(critical)
        plugin.add_summary("Unknown zk_server_state ({})".format(state))
    else:
        plugin.status(ok)
        plugin.add_summary("zk_server_state: {}".format(state))

    plugin.exit()

