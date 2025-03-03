# templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')

@register.filter
def format_number(value):
    try:
        num = float(value)
        return "{:,.0f}".format(num)
    except (ValueError, TypeError):
        return value
