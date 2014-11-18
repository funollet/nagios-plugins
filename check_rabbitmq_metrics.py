#!/usr/bin/env python
# check_rabbitmq_metrics.py
#
# Nagios plugin.

from pynag.Plugins import PluginHelper, ok, warning, critical, unknown
import requests


def show_response():
    """Shows items in a requests.Response. Mostly for debugging.
    """
    print "Url:      ", r.url
    print "HTTP code:", r.status_code
    print "Response: ", r.text
    print



if __name__ == '__main__':
    plugin = PluginHelper()
    plugin.parser.add_option('-H','--hostname', help="RabbitMQ host", default='127.0.0.1')
    plugin.parser.add_option('-p','--port', help="RabbitMQ port", default='15672')
    plugin.parser.add_option('--user', help="RabbitMQ user", default='guest')
    plugin.parser.add_option('--password', help="RabbitMQ password", default='guest')
    plugin.parse_arguments()

    # Auth for RabbitMQ REST API.
    auth = (plugin.options.user, plugin.options.password)
    # Build the metric URL.
    api = 'http://{}:{}/api/overview'.format(plugin.options.hostname, plugin.options.port)
    payload = { 
        'msg_rates_age': '3600',
        'msg_rates_incr': '10',
        'columns': 'message_stats.deliver_get_details.avg_rate',
    }

    # No need to specify a timeout: pynag has --timeout option for the whole plugin.
    r = requests.get(api, params=payload, auth=auth)

    if plugin.options.show_debug:
        show_response()

    if r.status_code == 401:
        plugin.add_summary("Login failed")
        plugin.exit()

    try:
        plugin.add_metric('deliver_rate', r.json()["message_stats"]["deliver_get_details"]["avg_rate"])
    except ValueError:
        plugin.add_summary("Can't decode server's response")
        plugin.exit()


    plugin.check_all_metrics()
    plugin.exit()

