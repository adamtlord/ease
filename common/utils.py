import googlemaps
import datetime

from django.conf import settings

METERS_TO_MILES = 0.000621371


def geocode_address(address_string):
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    geocode_result = gmaps.geocode(address_string)
    location = geocode_result[0]['geometry']['location']
    lat = location['lat']
    lng = location['lng']
    return (lat, lng)


def get_timezone(latlng):
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    timezone_result = gmaps.timezone(latlng)
    return timezone_result['timeZoneId']


def get_distance(ride):
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    if ride.start.ltlng:
        origins = ride.start.ltlng
    else:
        origins = ride.start.fulladdress

    if ride.destination.ltlng:
        destinations = ride.destination.ltlng
    else:
        destinations = ride.destination.fulladdress

    mode = 'driving'

    distance_in_miles = None

    try:
        distance_result = gmaps.distance_matrix(origins, destinations, mode=mode)
        distance_in_meters = distance_result['rows'][0]['elements'][0]['distance']['value']
        distance_in_miles = distance_in_meters * METERS_TO_MILES
    except:
        pass

    return distance_in_miles


def soon():
    soon = datetime.date.today() + datetime.timedelta(days=30)
    return {
        'month': soon.month,
        'year': soon.year
    }
