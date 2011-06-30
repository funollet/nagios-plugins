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
