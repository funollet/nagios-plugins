# Nagios-plugins 

Plugins for [Nagios](http://nagios.org/).

## check_gearmand_jobs.py

Checks the number of jobs in a Gearman queue.

    Usage: check_gearmand_jobs.py [options]

    Options:
      -h, --help            show this help message and exit
      -q QUEUE, --queue=QUEUE
                            Name of the queue to be checked
      -v VERBOSE, --verbose=VERBOSE
                            Verbosity Level
      -H HOST, --host=HOST  Target Host
      -t TIMEOUT, --timeout=TIMEOUT
                            Connection Timeout
      -c CRITICAL, --critical=CRITICAL
                            Critical Threshhold
      -w WARNING, --warning=WARNING
                            Warn Threshhold

## check_coraid.py

Checks status of a Coraid shelf. Runs commands `show -l`
and `list -l` and compares output with a previously stored file.

Requirements:

  * Coraid Ethernet Console (cec)
  * `pexpect` Python module

Before using the plugin for monitoring a Coraid device you must store its
output on a file to compare against. You can do it with the option `--create`.
Do it when the Coraid device is in good status.

Example:

    # check_coraid.py -i eth2 --shelf 0 --create

This plugin must run `cec` as root and, if there's a timeout, must be able to
kill it. That means you need something like this on your /etc/sudoers file.

    nagios  ALL= NOPASSWD: /usr/local/lib/nagios/plugins/check_coraid.py
  
This is giving full privileges to the script, so please check that no one can
overwrite the Nagios plugin neither the `cec` binary.

This script is inspired on [aoe-chk-coraid.sh](http://www.revpol.com/coraid_scripts) by William A. Arlofski.


    Usage: check_coraid.py <options>

    Options:
      -h, --help            show this help message and exit
      -s SHELF, --shelf=SHELF
                            number of the shelf (default: 0)
      -i INTERFACE, --interface=INTERFACE
                            interface to bind (default: eth0)
      -b BASEDIR, --basedir=BASEDIR
                            directory for baseline files (default:
                            /var/lib/check_coraid)
      -w, --show            show commands on stdout and exit
      -c, --create          create initial baseline file
      -d, --debug           show debugging info

