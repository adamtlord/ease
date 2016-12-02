from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def cc_display(value):
    mask_string = 'xxxx-' * 3
    return '{}{}'.format(mask_string, value)
