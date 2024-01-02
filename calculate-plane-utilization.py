#!/usr/bin/env python
#
# Calculate plane utilization based on "Flights / Check-ins" export in Flight Circle.
#
# nb: changing pilot names in Flight Circle causes the number of active pilots to be inflated.
#
# Copyright (c) 2022-2024, George A. Theall. All rights reserved.


############################################################################
import argparse
import csv
import datetime
import ephem
import logging
import sys

from dateutil.rrule import rrule, DAILY, WEEKLY


############################################################################
categories = {}
days = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday"
]
format = 'csv'

kpwm = ephem.Observer()
kpwm.pressure = 0
kpwm.horizon = '-0:34'
kpwm.lat, kpwm.lon = '43.65', '-70.31'  # nb: for KPWM

loglevel = 'INFO'


############################################################################
def calculate_time_diff(start, end):
  logging.debug("calculate_time_diff() : start : %s", str(start))
  logging.debug("calculate_time_diff() : end : %s", str(end))

  # in hours
  diff = round((end - start).total_seconds()/(60*60), 1)
  logging.debug("calculate_time_diff() :   diff: %.1f", diff)
  return diff


def main(args):
  # Read flight data.

  # nb: 'flights' will hold information about flights as well as maintenance reservations
  flights = {}
  date_ranges = {}
  active_pilots = {}
  active_pilots['_all_'] = {}
  active_pilots['_all_']['_all_'] = {}

  for file in args.files:
    with open(file, newline='') as csvfile:
      reader = csv.DictReader(csvfile)
      for row in reader:
        member = row['User']
        plane = row['Tail Number']
        # nb: ignore early records for test aircraft.
        if plane == 'G1' or plane == 'G2':
          continue
        if plane[:1] != 'N':
          plane = 'N' + plane
        if args.plane and plane != args.plane:
          continue

        restype = row['Reservation Type']
        depart = datetime.datetime.strptime(row['Depart Date'], '%Y-%m-%d %H:%M:%S')
        checkin = datetime.datetime.strptime(row['Check-in Date'], '%Y-%m-%d %H:%M:%S')

        logging.debug("Departure          : %s", str(depart))
        logging.debug("  Plane            : %s", plane)
        logging.debug("  Reservation type : %s", restype)
        logging.debug("  Member           : %s", member)
        logging.debug("  Check-in         : %s", str(checkin))

        if plane not in flights.keys():
          flights[plane] = {}
          date_ranges[plane] = {}
          active_pilots[plane] = {}
          active_pilots[plane]['_all_'] = {}

        # Itereate over each day of the flight since
        # flights can span days.
        for d in rrule(DAILY, dtstart=depart, until=checkin):
          logging.debug("    day : %s", str(d))

          # nb: track each planes first and last flight across all the data.
          if 'first' not in date_ranges[plane].keys():
            date_ranges[plane]['first'] = d.date()
            date_ranges[plane]['last'] = d.date()
          else:
            date_ranges[plane]['first'] = min(date_ranges[plane]['first'], d.date())
            date_ranges[plane]['last'] = max(date_ranges[plane]['last'], d.date())

          if d.date() == depart.date():
            start = depart.time()
          else:
            start = datetime.datetime.min.time()
          logging.debug("      start time : %s", str(start))

          if d.date() == checkin.date():
            end = checkin.time()
          else:
            end = datetime.datetime.max.time()
          logging.debug("      end time   : %s", str(end))

          if d.date() not in flights[plane].keys():
            flights[plane][d.date()] = []
          flights[plane][d.date()].append((member, restype, start, end))

  # Total times.
  #
  # nb: we categorize flight time into six possible buckets : 
  #   - weekday
  #     - daytime is between civilian sunrise and civilian sunset
  #     - evening is between civilian sunset and 10 pm
  #     - night is time before sunrise and after evening.
  #   - weekend
  #     - daytime
  #     - evening
  #     - night
  totals = {}

  totals['_all_'] = {}
  totals['_all_']['_all_'] = {}

  logging.debug("Totaling times")
  for k1 in ['dispatched', 'maintenance', 'possible']:
    totals['_all_']['_all_'][k1] = {}
    for k2 in ['weekday', 'weekend']:
      totals['_all_']['_all_'][k1][k2] = {}
      for k3 in ['day', 'evening', 'night']:
        totals['_all_']['_all_'][k1][k2][k3] = 0

  for plane in sorted(flights.keys()):
    logging.debug("  %s : ", plane)
    totals[plane] = {}

    totals[plane]['_all_'] = {}
    for k1 in ['dispatched', 'maintenance', 'possible']:
      totals[plane]['_all_'][k1] = {}
      for k2 in ['weekday', 'weekend']:
        totals[plane]['_all_'][k1][k2] = {}
        for k3 in ['day', 'evening', 'night']:
          totals[plane]['_all_'][k1][k2][k3] = 0

    if args.startdate:
      startdate = datetime.datetime.strptime(args.startdate, '%Y%m%d')
    else:
      startdate = date_ranges[plane]['first']
      logging.info("NB : start date for %s is %s.", plane, str(startdate))
    if args.enddate:
      enddate = datetime.datetime.strptime(args.enddate, '%Y%m%d')
    else:
      enddate = date_ranges[plane]['last']
      logging.info("NB : end date for %s is %s.", plane, str(enddate))

    for dt in rrule(DAILY, dtstart=startdate, until=enddate):
      logging.debug("    %s : ", str(dt))
      date = dt.date()

      yyyymm = date.strftime("%Y-%m")
      logging.debug("    %s : ", yyyymm)

      if yyyymm not in active_pilots['_all_'].keys():
        active_pilots['_all_'][yyyymm] = {}
      if yyyymm not in active_pilots[plane].keys():
        active_pilots[plane][yyyymm] = {}

      if yyyymm not in totals['_all_'].keys():
        totals['_all_'][yyyymm] = {}
        for k1 in ['dispatched', 'maintenance', 'possible']:
          totals['_all_'][yyyymm][k1] = {}
          for k2 in ['weekday', 'weekend']:
            totals['_all_'][yyyymm][k1][k2] = {}
            for k3 in ['day', 'evening', 'night']:
              totals['_all_'][yyyymm][k1][k2][k3] = 0

      if yyyymm not in totals[plane].keys():
        totals[plane][yyyymm] = {}
        for k1 in ['dispatched', 'maintenance', 'possible']:
          totals[plane][yyyymm][k1] = {}
          for k2 in ['weekday', 'weekend']:
            totals[plane][yyyymm][k1][k2] = {}
            for k3 in ['day', 'evening', 'night']:
              totals[plane][yyyymm][k1][k2][k3] = 0

      dow = days[date.weekday()]
      logging.debug("   day of week : %s", dow)
      if dow in ['Saturday', 'Sunday']:
        daytype = 'weekend'
      else:
        daytype = 'weekday'

      # Identify sunrise / sunset in Portland.
      #
      # nb: we use 2 pm here so "previous_rising" and "next_setting"
      #     refer to sunrise and sunset for the current day
      #     regardless of when the flight started.
      # nb: when I used 12 instead of 14 (2 pm) here, I would get
      #     sunrise dates for the _previous_ day starting around
      #     December 5 and running for several weeks. Possibly
      #     the ephem code is normalizing for DST and UTC.
      kpwm.date = datetime.datetime.combine(date, datetime.time(hour=14))
      sunrise = ephem.localtime(kpwm.previous_rising(ephem.Sun()))
      sunset = ephem.localtime(kpwm.next_setting(ephem.Sun()))
      logging.debug("  sunrise : %s", str(sunrise))
      logging.debug("  sunset : %s", str(sunset))
      if sunrise.date() != date:
        logging.warning("Previous sunrise is for a different day! (%s / %s)", str(date), str(sunrise.date()))
      if sunset.date() != date:
        logging.warning("Next sunset is for a different day! (%s / %s)", str(date), str(sunset.date()))
      # nb : and evening ends at 10 pm for our purposes.
      evening = datetime.datetime.combine(date, datetime.time(hour=22, minute=0))

      times = {}
      times['day'] = calculate_time_diff(sunrise, sunset)
      times['evening'] = calculate_time_diff(sunset, evening)
      times['night'] = calculate_time_diff(datetime.datetime.combine(date, datetime.datetime.min.time()), sunrise) +         calculate_time_diff(evening, datetime.datetime.combine(date, datetime.datetime.max.time()))
      logging.debug("     total daytime hours : %.1f", times['day'])
      logging.debug("     total evening hours : %.1f", times['evening'])
      logging.debug("     total nighttime hours : %.1f", times['night'])

      for k1 in ['_all_', plane]:
        for k2 in ['_all_', yyyymm]:
          for k3 in ['day', 'evening', 'night']:
            totals[k1][k2]['possible'][daytype][k3] = totals[k1][k2]['possible'][daytype][k3] + times[k3]

      if date not in flights[plane].keys():
        continue

      for (member, restype,start,end) in flights[plane][date]:
        logging.debug("    start : %s", str(start))
        logging.debug("      end : %s", str(end))
        logging.debug("      member : %s", member)
        logging.debug("      reservation type : %s", restype)

        if restype == 'Primary' or restype == 'Backup' or restype == 'intro flight':
          for k1 in ['_all_', plane]:
            for k2 in ['_all_', yyyymm]:
              if member not in active_pilots[k1][k2].keys():
                logging.debug("adding %s as an active pilot for %s for %s.", member, k1, k2)
                active_pilots[k1][k2][member] = {}
                active_pilots[k1][k2][member]['departures'] = []
              active_pilots[k1][k2][member]['departures'].append(datetime.datetime.combine(date, start))

        duration = calculate_time_diff(datetime.datetime.combine(date,start), datetime.datetime.combine(date,end))
        logging.debug("     duration : %.1f", duration)

        times = {}
        times['day'] = max( \
          0, \
          calculate_time_diff( \
            max(sunrise, datetime.datetime.combine(date,start)), \
            min(sunset, datetime.datetime.combine(date,end)) \
          ) \
        )
        times['night'] = max( \
          0, \
          calculate_time_diff( \
            datetime.datetime.combine(date,start), \
            min(sunrise, datetime.datetime.combine(date,end)) \
          ) \
        ) + \
        max( \
          0, \
          calculate_time_diff( \
            max(evening, datetime.datetime.combine(date,start)), \
            datetime.datetime.combine(date,end) \
          ) \
        )
        times['evening'] = round(duration - times['day'] - times['night'], 1)
        logging.debug("     daytime hours : %.1f", times['day'])
        logging.debug("     evening hours : %.1f", times['evening'])
        logging.debug("     nighttime hours : %.1f", times['night'])

        if restype == 'Primary' or restype == 'Backup' or restype == 'intro flight':
          k3 = 'dispatched'
        elif restype == 'Maintenance' or restype == 'transport':
          k3 = 'maintenance'
        else:
          logging.warning("Ignoring unexpected reservation type (%s)!", restype)
          continue

        for k1 in ['_all_', plane]:
          for k2 in ['_all_', yyyymm]:
            for k4 in ['day', 'evening', 'night']:
              totals[k1][k2][k3][daytype][k4] = totals[k1][k2][k3][daytype][k4] + times[k4]

  # Calculate / output utilization rates
  if args.format == 'csv':
    writer = csv.writer(sys.stdout, quoting=csv.QUOTE_NONNUMERIC)
    for plane in sorted(flights.keys()):
      for yyyymm in sorted(totals[plane].keys()):
        if yyyymm == '_all_':
          continue
        writer.writerow([plane, yyyymm, 'active pilots', len(active_pilots[plane][yyyymm].keys())])

        for k1 in ['possible', 'maintenance', 'dispatched']:
          cells = []
          for k2 in ['weekday', 'weekend']:
            for k3 in ['day', 'evening', 'night']:
              cells.append(float(" %.1f" % (totals[plane][yyyymm][k1][k2][k3])))
          writer.writerow([plane, yyyymm, k1 + ' hours'] + cells)
        cells = []
        for k2 in ['weekday', 'weekend']:
          for k3 in ['day', 'evening', 'night']:
            if round(totals[plane][yyyymm]['possible'][k2][k3] - totals[plane][yyyymm]['maintenance'][k2][k3], 1) == 0:
              cells.append(" n/a")
            else:
              rate = 100 * totals[plane][yyyymm]['dispatched'][k2][k3] / (totals[plane][yyyymm]['possible'][k2][k3] - totals[plane][yyyymm]['maintenance'][k2][k3])
              cells.append(float(" %6.1f" % rate))
        writer.writerow([plane, yyyymm, 'utilization rate'] + cells)

      if args.aggregate == 'time' or args.aggregate == 'both':
        writer.writerow([plane, 'all time', 'active pilots', len(active_pilots[plane]['_all_'].keys())])
        for k1 in ['possible', 'maintenance', 'dispatched']:
          cells = []
          for k2 in ['weekday', 'weekend']:
            for k3 in ['day', 'evening', 'night']:
              cells.append(float(" %.1f" % (totals[plane]['_all_'][k1][k2][k3])))
          writer.writerow([plane, 'all time', k1 + ' hours'] + cells)
        cells = []
        for k2 in ['weekday', 'weekend']:
          for k3 in ['day', 'evening', 'night']:
            if round(totals[plane]['_all_']['possible'][k2][k3] - totals[plane]['_all_']['maintenance'][k2][k3], 1) == 0:
              cells.append(" n/a")
            else:
              rate = 100 * totals[plane]['_all_']['dispatched'][k2][k3] / (totals[plane]['_all_']['possible'][k2][k3] - totals[plane]['_all_']['maintenance'][k2][k3])
              cells.append(float(" %6.1f" % rate))
        writer.writerow([plane, 'all time', 'utilization rate'] + cells)

    if args.aggregate == 'planes' or args.aggregate == 'both':
      for yyyymm in sorted(totals['_all_'].keys()):
        if yyyymm == '_all_':
          continue
        writer.writerow(['all planes', yyyymm, 'active pilots', len(active_pilots['_all_'][yyyymm].keys())])

        for k1 in ['possible', 'maintenance', 'dispatched']:
          cells = []
          for k2 in ['weekday', 'weekend']:
            for k3 in ['day', 'evening', 'night']:
              cells.append(float(" %.1f" % (totals['_all_'][yyyymm][k1][k2][k3])))
          writer.writerow(['all planes', yyyymm, k1 + ' hours'] + cells)
        cells = []
        for k2 in ['weekday', 'weekend']:
          for k3 in ['day', 'evening', 'night']:
            if round(totals['_all_'][yyyymm]['possible'][k2][k3] - totals['_all_'][yyyymm]['maintenance'][k2][k3], 1) == 0:
              cells.append(" n/a")
            else:
              rate = 100 * totals['_all_'][yyyymm]['dispatched'][k2][k3] / (totals['_all_'][yyyymm]['possible'][k2][k3] - totals['_all_'][yyyymm]['maintenance'][k2][k3])
              cells.append(float(" %6.1f" % rate))
        writer.writerow(['all planes', yyyymm, 'utilization rate'] + cells)
      if args.aggregate == 'time' or args.aggregate == 'both':
        writer.writerow(['all planes', 'all time', 'active pilots', len(active_pilots['_all_']['_all_'].keys())])
        for k1 in ['possible', 'maintenance', 'dispatched']:
          cells = []
          for k2 in ['weekday', 'weekend']:
            for k3 in ['day', 'evening', 'night']:
              cells.append(float(" %.1f" % (totals['_all_']['_all_'][k1][k2][k3])))
          writer.writerow(['all planes', 'all time', k1 + ' hours'] + cells)
        cells = []
        for k2 in ['weekday', 'weekend']:
          for k3 in ['day', 'evening', 'night']:
            if round(totals['_all_']['_all_']['possible'][k2][k3] - totals['_all_']['_all_']['maintenance'][k2][k3], 1) == 0:
              cells.append(" n/a")
            else:
              rate = 100 * totals['_all_']['_all_']['dispatched'][k2][k3] / (totals['_all_']['_all_']['possible'][k2][k3] - totals['_all_']['_all_']['maintenance'][k2][k3])
              cells.append(float(" %6.1f" % rate))
        writer.writerow(['all planes', 'all time', 'utilization rate'] + cells)
  elif args.format == 'txt':
    for plane in sorted(flights.keys()):
      print(plane + " : ")

      for yyyymm in sorted(totals[plane].keys()):
        if yyyymm == '_all_':
          continue

        print("  " + yyyymm + " : ")

        print("    Active pilots : ", len(active_pilots[plane][yyyymm].keys()))

        for k1 in ['possible', 'maintenance', 'dispatched']:
          print("    " + k1 + " (hours) : ", end="")
          for k2 in ['weekday', 'weekend']:
            for k3 in ['day', 'evening', 'night']:
              print(" %.1f" % (totals[plane][yyyymm][k1][k2][k3]), end="")
          print()
        print("    Utilization (%) : ", end="")
        for k2 in ['weekday', 'weekend']:
          for k3 in ['day', 'evening', 'night']:
            if round(totals[plane][yyyymm]['possible'][k2][k3] - totals[plane][yyyymm]['maintenance'][k2][k3], 1) == 0:
              print("n/a", end="")
            else:
              rate = 100 * totals[plane][yyyymm]['dispatched'][k2][k3] / (totals[plane][yyyymm]['possible'][k2][k3] - totals[plane][yyyymm]['maintenance'][k2][k3])
              print(" %6.1f" % rate, end="")
        print()
      if args.aggregate == 'time' or args.aggregate == 'both':
        print("  " + 'all time' + " : ")

        print("    Active pilots : ", len(active_pilots[plane]['_all_'].keys()))

        for k1 in ['possible', 'maintenance', 'dispatched']:
          print("    " + k1 + " (hours) : ", end="")
          for k2 in ['weekday', 'weekend']:
            for k3 in ['day', 'evening', 'night']:
              print(" %.1f" % (totals[plane]['_all_'][k1][k2][k3]), end="")
          print()
        print("    Utilization (%) : ", end="")
        for k2 in ['weekday', 'weekend']:
          for k3 in ['day', 'evening', 'night']:
            if round(totals[plane]['_all_']['possible'][k2][k3] - totals[plane]['_all_']['maintenance'][k2][k3], 1) == 0:
              print("n/a", end="")
            else:
              rate = 100 * totals[plane]['_all_']['dispatched'][k2][k3] / (totals[plane]['_all_']['possible'][k2][k3] - totals[plane]['_all_']['maintenance'][k2][k3])
              print(" %6.1f" % rate, end="")
      print()
    if args.aggregate == 'planes' or args.aggregate == 'both':
      print("All planes : ")
      for yyyymm in sorted(totals['_all_'].keys()):
        if yyyymm == '_all_':
          continue
        print("  " + yyyymm + " : ")

        print("    Active pilots : ", len(active_pilots['_all_'][yyyymm].keys()))

        for k1 in ['possible', 'maintenance', 'dispatched']:
          print("    " + k1 + " (hours) : ", end="")
          for k2 in ['weekday', 'weekend']:
            for k3 in ['day', 'evening', 'night']:
              print(" %.1f" % totals['_all_'][yyyymm][k1][k2][k3], end="")
          print()
        print("    Utilization (%) : ", end="")
        for k2 in ['weekday', 'weekend']:
          for k3 in ['day', 'evening', 'night']:
              if round(totals['_all_'][yyyymm]['possible'][k2][k3] - totals['_all_'][yyyymm]['maintenance'][k2][k3], 1) == 0:
                print("n/a", end="")
              else:
                rate = 100 * totals['_all_'][yyyymm]['dispatched'][k2][k3] / (totals['_all_'][yyyymm]['possible'][k2][k3] - totals['_all_'][yyyymm]['maintenance'][k2][k3])
                print(" %6.1f" % rate, end="")
        print()
      if args.aggregate == 'time' or args.aggregate == 'both':
        print("  " + 'all time' + " : ")

        print("    Active pilots : ", len(active_pilots['_all_']['_all_'].keys()))

        for k1 in ['possible', 'maintenance', 'dispatched']:
          print("    " + k1 + " (hours) : ", end="")
          for k2 in ['weekday', 'weekend']:
            for k3 in ['day', 'evening', 'night']:
              print(" %.1f" % (totals['_all_']['_all_'][k1][k2][k3]), end="")
          print()
        print("    Utilization (%) : ", end="")
        for k2 in ['weekday', 'weekend']:
          for k3 in ['day', 'evening', 'night']:
            if round(totals['_all_']['_all_']['possible'][k2][k3] - totals['_all_']['_all_']['maintenance'][k2][k3], 1) == 0:
              print("n/a", end="")
            else:
              rate = 100 * totals['_all_']['_all_']['dispatched'][k2][k3] / (totals['_all_']['_all_']['possible'][k2][k3] - totals['_all_']['_all_']['maintenance'][k2][k3])
              print(" %6.1f" % rate, end="")
        print()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Calculate plane utilization rates.')
  parser.add_argument('-a', '--aggregate', choices=['planes', 'time', 'both'], help='Output aggregate rates.', nargs='?')
  parser.add_argument('-e', '--enddate', help='End date (yyyymmdd).', nargs='?')
  parser.add_argument('-f', '--format', default=format, choices=['csv', 'txt'], help='Output format.', nargs='?')
  parser.add_argument('-l', '--loglevel', default=loglevel, help='Level for logging messages.', nargs='?')
  parser.add_argument('-p', '--plane', help='Limit attention to a specific plane.', nargs='?')
  parser.add_argument('-s', '--startdate', help='Start date (yyyymmdd).', nargs='?')
  parser.add_argument("files", help="Flight / check-in export file", nargs='+')
  args = parser.parse_args()

  if not isinstance(getattr(logging, args.loglevel.upper(), None), int):
    raise ValueError("Invalid log level '%s'", args.loglevel)
  logging.basicConfig(level=getattr(logging, args.loglevel.upper(), None))
  logger = logging.getLogger(__name__)

  main(args)
