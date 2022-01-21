"""Console script for boschalarm."""
import logging
import sys
import time

from docopt import docopt

from codes import *
from main import Bosch


def main():
    """Bosch b426 API client

    Usage:
      cli.py [-v] --ip IP [--port PORT]

    Options:
        -h --help       Show this screen.
        --ip IP         The IP address of the Bosch 426 module
        --port PORT     Specify the port to use [default: 7700].
        -v --verbose    Increase output

    """

    args = docopt(main.__doc__, version='0.1')
    if args['--verbose']:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Connnect to the unit
    b = Bosch(args['--ip'], args['--port'])

    # Pin check works
    b.checkpin()

    # Arming seems to raise an authorisation error
    b.armAreas(ArmingType.Disarm)

    b.requestAlarmDetail(AlarmTypes.BurglaryTrouble.value)

    b.requestAreasNotReady()

    b.getStatus()

    # This check works, you can run it in a loop
    for i in range(3):
        b.requestFaultedPoints()
        time.sleep(2)

    # This doesn't seem to work
    b.subscribe()
    b.requestSubscriptions()

    # This doesn't seem to work
    b.getReport(test_report=False)
    b.getReport(test_report=True)

    # This doesn't seem to work
    b.requestAlarmPriorities()

    for i in b.configured_areas:
        b.requestAreaText(i)
        b.RequestAlarmAreasByPriority(i)  # Not working
        b.requestAreaStatus(i)
        b.silenceAlarms(i)

    b.requestOutputStatus()
    for i in range(4):
        b.requestOutputText(i)

    b.close()

if __name__ == "__main__":

    sys.exit(main())  # pragma: no cover
