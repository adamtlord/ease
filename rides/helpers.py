import csv
from datetime import datetime
import pytz
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from rides.models import Ride

LYFT_COLUMNS = (
    ('Request time'),
    ('Name'),
    ('Payment'),
    ('Amount'),
    ('Pickup'),
    ('Dropoff'),
    ('Note'),
    ('Internal Note'),
)

ID_COL = LYFT_COLUMNS[7]
COST_COL = LYFT_COLUMNS[3]
REQUEST_TIME_COL = LYFT_COLUMNS[0]
LYFT_DATETIME_FORMAT = '%m/%d/%y %H:%M'


def handle_lyft_upload(uploaded_file):

    results = {
        'warnings': [],
        'errors': [],
        'success': 0,
        'total': 0
    }

    reader = csv.DictReader(uploaded_file)
    for idx, row in enumerate(reader):
        results['total'] += 1
        try:
            ride_id = int(row[ID_COL])
            ride = Ride.objects.get(pk=ride_id)
            ride.complete = True
            ride.cost = Decimal(row[COST_COL].replace('$', '').strip(' '))
            try:
                ride.request_time = pytz.utc.localize(datetime.strptime(row[REQUEST_TIME_COL], LYFT_DATETIME_FORMAT))
            except:
                pass
            ride.save()
            results['success'] += 1
        except ValueError:
            results['errors'].append('Row {}: Can\'t find an ID number in the "{}" column ("{}")'.format(idx + 1, ID_COL, row[ID_COL]))
        except ObjectDoesNotExist:
            results['errors'].append('Row {}: Can\'t find a Ride with the ID provided ({})'.format(idx + 1, ride_id))

    return results
