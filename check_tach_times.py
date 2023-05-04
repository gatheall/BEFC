#!/usr/bin/env python
#
# Make sure that tach times add up for planes based on "Flights / Check-ins" export in Flight Circle.
#
# Copyright (c) 2022, George A. Theall. All rights reserved.


############################################################################
import argparse
import csv
import datetime
import logging
import sys

from dateutil.rrule import rrule, DAILY, WEEKLY


############################################################################
categories = {}

loglevel = 'WARNING'


############################################################################
def main(args):
  # Read flight data.

  tts = {}

  for file in args.files:
    with open(file, newline='') as csvfile:
      reader = csv.DictReader(csvfile)
      for row in reader:
        plane = row['Tail Number']
        # nb: ignore early records for test aircraft.
        if plane == 'G1' or plane == 'G2':
          continue
        if plane[:1] != 'N':
          plane = 'N' + plane
        if args.plane and plane != args.plane:
          continue
        if plane not in tts.keys():
          tts[plane] = []

        member = row['User']

        tt_in = round(float(row['Tach-In']), 2)
        tt_out = round(float(row['Tach-Out']), 2)
        tt = round(float(row['Tach Total']), 2)

        restype = row['Reservation Type']
        depart = datetime.datetime.strptime(row['Depart Date'], '%Y-%m-%d %H:%M:%S')

        logging.debug("Departure          : %s", str(depart))
        logging.debug("  Plane            : %s", plane)
        logging.debug("  Reservation type : %s", restype)
        logging.debug("  Member           : %s", member)
        logging.debug("  TT               : %f", tt)
        logging.debug("  Tach out         : %f", tt_out)
        logging.debug("  Tach in          : %f", tt_in)

        if round(tt_in - tt_out, 2) != tt:
          logging.warning("Reported tach time doesn't match calculated tach time for %s / %s - (%.2f-%.2f) != %.2f", plane, str(depart), tt_in, tt_out, tt)

        if (tts[plane]):
          tt_prev = tts[plane][-1]
          if tt_prev != tt_out:
            logging.warning("Previous TT on check-in differs from current TT on dispatch for %s / %s - %.2f != %.2f", plane, str(depart), tt_prev, tt_out)

        tts[plane].append(tt_in)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Check plane tach times.')
  parser.add_argument('-l', '--loglevel', default=loglevel, help='Level for logging messages.', nargs='?')
  parser.add_argument('-p', '--plane', help='Limit attention to a specific plane.', nargs='?')
  parser.add_argument("files", help="Flight / check-in export file", nargs='+')
  args = parser.parse_args()

  if not isinstance(getattr(logging, args.loglevel.upper(), None), int):
    raise ValueError("Invalid log level '%s'", args.loglevel)
  logging.basicConfig(level=getattr(logging, args.loglevel.upper(), None))
  logger = logging.getLogger(__name__)

  main(args)
