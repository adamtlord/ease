import csv
from datetime import datetime
import pytz
from collections import OrderedDict
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from rides.models import Ride

LYFT_COLUMNS = [
    'Amount',
    'Ride ID',
    'Company'
]

COST_COL = LYFT_COLUMNS[0]
ID_COL = LYFT_COLUMNS[1]
COMPANY_COL = LYFT_COLUMNS[2]
LYFT_DATETIME_FORMAT = '%m/%d/%y %H:%M'


def handle_lyft_upload(uploaded_file):

    results = {
        'warnings': [],
        'errors': [],
        'success': 0,
        'total': 0
    }

    reader = csv.DictReader(uploaded_file, fieldnames=LYFT_COLUMNS)
    headers = next(reader)
    for idx, row in enumerate(reader):
        results['total'] += 1
        try:
            ride_id = int(row[ID_COL])
            ride = Ride.objects.get(pk=ride_id)
            ride.cost = Decimal(row[COST_COL].replace('$', '').strip(' '))
            if row[COMPANY_COL]:
                ride.company = row[COMPANY_COL].title()
            ride.complete = True
            ride.save()
            results['success'] += 1
        except ValueError:
            results['errors'].append('Row {}: Can\'t find an ID number in the "{}" column ("{}")'.format(idx + 1, ID_COL, row[ID_COL]))
        except ObjectDoesNotExist:
            results['errors'].append('Row {}: Can\'t find a Ride with the ID provided ({})'.format(idx + 1, ride_id))

    return results


def sort_rides_by_customer(rides):
    customers = dict()

    if rides:
        for r in rides:
            if r.customer in customers:
                customers[r.customer].append(r)
            else:
                customers[r.customer] = [r]
        customers = OrderedDict(sorted(customers.items(), key=lambda t: t[0].last_name))
    return customers


def sort_rides_by_ride_account(rides):
    accounts = dict()
    """
        {
            account: {
                customer: [
                    ride,
                    ride
                ],
                customer: [
                    ride,
                    ride,
                    ride
                ]
            },
            account: {
                customer: [
                    ride
                ]
            }
        }
    """
    if rides:
        for r in rides:

            if r.customer.group_bill:
                account = r.customer.group_membership.ride_account
            else:
                account = r.customer.ride_account

            if account in accounts:
                if r.customer in accounts[account]:
                    accounts[account][r.customer].append(r)
                else:
                    accounts[account][r.customer] = [r]
            else:
                accounts[account] = {r.customer: [r]}

    return accounts
