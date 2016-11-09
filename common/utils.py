import googlemaps
from django.conf import settings


def geocode_address(address_string):
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    geocode_result = gmaps.geocode(address_string)
    location = geocode_result[0]['geometry']['location']
    lat = location['lat']
    lng = location['lng']
    return (lat, lng)
