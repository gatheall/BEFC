#!/usr/bin/env python
#
# Track changes in member balances (ie, charges and payments) by month based on "Sales Transactions" export in Flight Circle.
#
# Copyright (c) 2023, George A. Theall. All rights reserved.


############################################################################
import argparse
import csv
import datetime
import logging
import sys


############################################################################
format = 'csv'

loglevel = 'WARNING'


############################################################################
def main(args):
  # Read transaction data

  # nb: 'flights' will hold information about flights as well as maintenance reservations
  transactions = {}
  members = {}

  for file in args.files:
    with open(file, newline='') as csvfile:
      reader = csv.DictReader(csvfile)
      for row in reader:
        dt = datetime.datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
        logging.debug("Date                 : %s", str(dt))
        transaction_type = row['Type']
        member = " ".join([row['First Name'],row['Last Name']])
        logging.debug("  Member             : %s", member)
        if member not in members.keys():
          members[member] = {}

        transaction_desc = row['Description']
        logging.debug("    Transaction type : %s / %s", transaction_type, transaction_desc)
        if transaction_type == 'Payment':
          amt = round(float(row['Payment']), 2)
        elif transaction_type == 'Charge':
          if "(Non Revenue)" in transaction_desc:
            continue
          elif transaction_desc == 'Surcharge' or transaction_desc == 'Service Fee':
            transaction_type = 'Payment'
            amt = -1 * round(float(row['Adjustment']), 2)
          else:
            amt = round(float(row['Charge']), 2)
        elif transaction_type == 'Adjustment':
            transaction_type = 'Payment'
            amt = abs(round(float(row['Adjustment']), 2))
        logging.debug("    Amt              : %.2f", amt)

        monyy =  dt.strftime("%Y-%m")
        if monyy not in transactions.keys():
          transactions[monyy] = {}
        if member not in transactions[monyy].keys():
          transactions[monyy][member] = {}
          transactions[monyy][member]['charges'] = []
          transactions[monyy][member]['payments'] = []
        if transaction_type == 'Charge':
          transactions[monyy][member]['charges'].append(str(amt))
        if transaction_type == 'Payment':
          transactions[monyy][member]['payments'].append(str(amt))

  for member in sorted(members.keys()):
    print("  " + member + " : ")
    for monyy in sorted(transactions.keys()):
      if not member in transactions[monyy].keys():
        continue
      print(monyy + " : ")
      print("    Charges : " + "=" + "+".join(transactions[monyy][member]['charges']))
      print("    Payments : " + "=" + "+".join(transactions[monyy][member]['payments']))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Track changes in member balances.')
  parser.add_argument('-l', '--loglevel', default=loglevel, help='Level for logging messages.', nargs='?')
  parser.add_argument("files", help="'Sales Transactions' report file", nargs='+')
  args = parser.parse_args()

  if not isinstance(getattr(logging, args.loglevel.upper(), None), int):
    raise ValueError("Invalid log level '%s'", args.loglevel)
  logging.basicConfig(level=getattr(logging, args.loglevel.upper(), None))
  logger = logging.getLogger(__name__)

  main(args)
