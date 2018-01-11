import datetime
import locale
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def cc_display(value):
    mask_string = 'xxxx-' * 3
    return '{}{}'.format(mask_string, value)


@register.filter
def from_timestamp(value):
    return datetime.datetime.fromtimestamp(value)


@register.filter(name='currency')
def currency(value):
    if not value:
        return '--'
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        locale.setlocale(locale.LC_ALL, '')
    loc = locale.localeconv()
    return locale.currency(value, loc['currency_symbol'], grouping=True)
