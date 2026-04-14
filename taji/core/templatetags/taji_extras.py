from django import template
from django.conf import settings

register = template.Library()

@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)

@register.simple_tag
def settings_value(name):
    return getattr(settings, name, '')
