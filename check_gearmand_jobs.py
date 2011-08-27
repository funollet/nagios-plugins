#!/usr/bin/env python
# -*- coding:utf-8 -*-
# check_gearmand_jobs.py
"""

Nagios plugin, checks the number of jobs in a Gearman queue.
"""

# Copyright 2011 Jordi Funollet <jordi.f@ati.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import telnetlib
import socket
import os
from optparse import OptionParser


DEBUG_MOCK_GEARMAND = False


############################################################

class Plugin:
    """
    Nagios plugin helper library based on Nagios::Plugin
    """

    def __init__(self, shortname = None, version = None, blurb = None, extra = None, url = None, license = None, plugin = None, timeout = 15 ):

        ## this is the custom parser
        self.extra_list_optional = []
        self.extra_list_required = []

        ## Set the option parser stuff here
        self.parser = OptionParser()

        ## Variables we'll get later
        self.opts = None
        self.data = {}
        self.data['threshhold'] = None

        ## Error mappings, for easy access
        self.errors = { "OK":0, "WARNING":1, "CRITICAL":2, "UNKNOWN":3, }
        self.status_text = { 0:"OK", 1:"WARNING", 2:"CRITICAL", 3:"UNKNOWN", }

        ## Shortname creation
        if not shortname:
            self.data['shortname'] = os.path.basename("%s" % sys.argv[0])
        else:
            self.data['shortname'] = shortname

        ## Status messages
        self.data['messages'] = { "warning":None, "critical":None, "ok":None }



    def add_arg(self, spec_abbr, spec, help_text, required=1):
        """
        Add an argument to be handled by the option parser. 
        By default, the arg is not required
        """
        self.parser.add_option("-%s" % spec_abbr, "--%s" % spec, 
                dest="%s" % spec, help=help_text, metavar="%s" % spec.upper())
        if required:
            self.extra_list_required.append(spec)
        else:
            self.extra_list_optional.append(spec)



    def activate(self):
        """
        Parse out all command line options and get ready to process the plugin.
        This should be run after argument preps
        """
        timeout = None
        verbose = 0

        self.parser.add_option("-v", "--verbose", dest="verbose", 
                help="Verbosity Level", metavar="VERBOSE", default=0)
        self.parser.add_option("-H", "--host", dest="host", 
                help="Target Host", metavar="HOST")
        self.parser.add_option("-t", "--timeout", dest="timeout", 
                help="Connection Timeout", metavar="TIMEOUT")
        self.parser.add_option("-c", "--critical", dest="critical", 
                help="Critical Threshhold", metavar="CRITICAL")
        self.parser.add_option("-w", "--warning", dest="warning", 
                help="Warn Threshhold", metavar="WARNING")

        (options, args) = self.parser.parse_args()

        ## Set verbosity level
        if int(options.verbose) in (0, 1, 2, 3):
            self.data['verbosity'] = options.verbose
        else:
            self.data['verbosity'] = 0

        ## Ensure the hostname is set
        if options.host:
            self.data['host'] = options.host
        else:
            self.data['host'] = 'localhost'

        ## Set timeout
        if options.timeout:
            self.data['timeout'] = options.timeout
        else:
            self.data['timeout'] = timeout

        if not options.critical and not options.warning:
            self.parser.error("You must provide a WARNING and/or CRITICAL value")

        ## Set Critical
        if options.critical:
            self.data['critical'] = options.critical
        else: self.data['critical'] = None

        ## Set Warn
        if options.warning:
            self.data['warning'] = options.warning
        else:
            self.data['warning'] = None

        ## Ensurethat the extra items are provided
        for extra_item in self.extra_list_required:
            if not options.__dict__[extra_item]:
                self.parser.error("option '%s' is required" % extra_item)


        ## Put the remaining values into the data dictionary
        for key,value in options.__dict__.items():
            if key in (self.extra_list_required + self.extra_list_optional):
                self.data[key] = value



    def check_range(self, value):
        """
        Check if a value is within a given range.  This should replace change_threshold eventually

        Taken from:  http://nagiosplug.sourceforge.net/developer-guidelines.html
        Range definition
    
        Generate an alert if x...
        10      < 0 or > 10, (outside the range of {0 .. 10})
        10:     < 10, (outside {10 .. #})
        ~:10    > 10, (outside the range of {-# .. 10})
        10:20   < 10 or > 20, (outside the range of {10 .. 20})
        @10:20  # 10 and # 20, (inside the range of {10 .. 20})
        """
        critical = self.data['critical']
        warning = self.data['warning']

        if critical and self._range_checker(value, critical):
            self.nagios_exit("CRITICAL","%s meets the range: %s" % (value, self.hr_range))

        if warning and self._range_checker(value, warning):
            self.nagios_exit("WARNING","%s meets the range: %s" % (value, self.hr_range))

        ## This is the lowest range, which we'll output
        if warning:
            alert_range = warning
        else:
            alert_range = critical
        
        self.nagios_exit("OK","%s does not meet the range: %s" % (value, self.hr_range))



    def _range_checker(self, value, check_range):
        """
        Builtin check using nagios development guidelines
        """
        import re

        ## Simple number check
        simple_num_re = re.compile('^\d+$')
        if simple_num_re.match(str(check_range)):
            self.hr_range = "> %s" % check_range
            value = float(value)
            check_range = float(check_range)
            if (value < 0) or (value > check_range):
                return True
            else:
                return False

        if (check_range.find(":") != -1) and (check_range.find("@") == -1):
            (start, end) = check_range.split(":")

            ## 10:     < 10, (outside {10 .. #})
            if (end == "") and (float(value) < float(start)):
                self.hr_range = "< %s" % (start)
                return True
            elif (end == "") and (float(value) >= float(start)):
                self.hr_range = "< %s" % (start)
                return False

            ## ~:10    > 10, (outside the range of {-# .. 10})
            if (start == "~") and (float(value) > float(end)):
                self.hr_range = "> %s" % (end)
                return True
            elif (start == "~") and (float(value) <= float(end)):
                self.hr_range = "> %s" % (end)
                return False

            ## 10:20   < 10 or > 20, (outside the range of {10 .. 20})
            if (start < float(value)) or (end > float(value)):
                self.hr_range = "< %s or > %s" % (start,end)
                return True
            else:
                self.hr_range = "< %s or > %s" % (start,end)
                return False

        ## Inclusive range check
        if check_range[0] == "@":
            (start, end) = check_range[1:].split(":")
            start = float(start)
            end = float(end)
            self.hr_range = "Between %s and %s" % (start, end)
            if ( float(value) >= start ) and ( float(value) <= end ):
                return True
            else:
                return False



    def nagios_exit(self, code_text, message):
        """
        Exit with exit_code, message, and optionally perfdata
        """
        ## This should be one line (or more in nagios 3)
        print "%s : %s" % (code_text, message)
        sys.exit(self.errors[code_text])

    def __setitem__(self, key, item):
        self.data[key] = item

    def __getitem__(self, key):
        return self.data[key]


############################################################

def parse_gearmand_status(raw_status):
    """Builds dict from a Gearmand 'status' string.
    
    { queue_name: ( total_jobs, running_jobs, available_workers ) }
    """
    lines = [ ( line.split()[0], line.split()[1:] ) 
            for line in raw_status.split('\n') if line not in ['', '.'] ]
    return dict(lines)



def get_gearmand_status(host='localhost', port=4730, timeout=0.5):
    """Connects to 'port' and retrieves the 'status' of Gearmand.
    """
    client = telnetlib.Telnet(host, port)
    client.write('status\n')
    raw_status = client.expect(['^.$'], timeout)
    client.close()
    return raw_status[2]


def mock_get_gearmand_status():
    """Simulate get_gearmand_status() interface, just for testing.
    """
    return '''
vocaloid        8       0       9
send_email      0       0       2
parallel_processing     0       0       1
callback        0       0       2
essentia        0       0       9
audio_conversion        0       0       9
add_file_to_collection  0       0       2
save_conversion 0       0       3
save_analysis   0       0       3
wav2png 0       0       9
audio_properties        0       0       9
voice_transformation    0       0       9
.
'''


def main():
    """Run unless imported.
    """

    plugin = Plugin()
    plugin.add_arg("q", "queue", "Name of the queue to be checked")
    plugin.add_arg("p", "port", "Port to connect (default: 4730)",
            required = False)
    plugin.activate()
    if not plugin['port']:
        plugin['port'] = 4730


    if DEBUG_MOCK_GEARMAND:
        raw_status = mock_get_gearmand_status()
    else:
        try:
            # String with Gearmand's output for command 'status'.
            raw_status = get_gearmand_status(plugin['host'], plugin['port'])
        except socket.error:
            plugin.nagios_exit("UNKNOWN", "Failed connection")
            
    # Dict with one key for every queue.
    status = parse_gearmand_status(raw_status)

    if not status.has_key (plugin['queue']):
        plugin.nagios_exit("UNKNOWN", "Queue %s not found" % plugin['queue'])

    total_jobs = status[plugin['queue']][0]
    plugin.check_range(total_jobs)

    return 0




############################################################

def test():
    """Miscelaneous tests used for debugging.
    """
    assert parse_gearmand_status('') == {}
    assert parse_gearmand_status('.') == {}
    assert parse_gearmand_status('audio_conversion    0       0       9') \
        == {'audio_conversion': ['0', '0', '9']}
    assert parse_gearmand_status('''
vocaloid        0       0       9
send_email      0       0       2
.'''
        ) == {'vocaloid': ['0', '0', '9'], 'send_email': ['0', '0', '2']}

    ___ = parse_gearmand_status(mock_get_gearmand_status())
    
    print get_gearmand_status()
    

############################################################

if __name__ == '__main__':
    #test()
    sys.exit(main())
    

