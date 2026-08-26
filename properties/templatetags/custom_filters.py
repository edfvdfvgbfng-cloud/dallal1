"""
Custom template filters for the Dalal project
"""

from django import template

register = template.Library()


@register.filter
def number_format(value):
    """
    Format a number with thousand separators
    """
    if value is None:
        return '0'
    
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return str(value)