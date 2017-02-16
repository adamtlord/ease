from django import template
from django.conf import settings
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def static_map(address):
    if address.latitude and address.longitude:
        return format_html('<div class="static-map"><img src="https://maps.googleapis.com/maps/api/staticmap?&zoom=14&size=360x270&scale=2&markers=color:0x0346b2|{},{}&key={}" class="img-responsive" /></div>',
                           address.latitude,
                           address.longitude,
                           settings.GOOGLE_MAPS_API_KEY
                           )
    else:
        return format_html('<div class="static-map"><div class="error">Unable to map this address!</div></div>')
