"""
Custom template filters for the Dalal project
"""

import itertools
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


@register.filter
def can_edit_contract(contract, user):
    """
    Check if a user can edit a contract
    """
    if hasattr(contract, 'can_edit'):
        return contract.can_edit(user)
    return False


@register.filter
def can_delete_contract(contract, user):
    """
    Check if a user can delete a contract
    """
    if hasattr(contract, 'can_delete'):
        return contract.can_delete(user)
    return False


@register.filter
def can_view_contract(contract, user):
    """
    Check if a user can view a contract
    """
    if hasattr(contract, 'can_view'):
        return contract.can_view(user)
    return False


@register.filter(name='range')
def filter_range(value):
    """
    Filter to return range(0, value) for use in for loops:
    {% for i in 5|range %}
    """
    try:
        return range(max(0, int(value)))
    except (ValueError, TypeError):
        return range(0)


@register.filter
def times(number, max_val=None):
    """
    Return range(number) or range(min(number, max_val)).
    {% for i in rating|times:5 %}
    """
    try:
        n = int(number)
        if max_val is not None:
            n = min(n, int(max_val))
        return range(max(0, n))
    except (ValueError, TypeError):
        return range(0)


@register.filter
def times_remaining(number, total=5):
    """
    Return range for remaining empty stars:
    {% for i in rating|times_remaining:5 %}
    """
    try:
        rem = int(total) - int(number)
        return range(max(0, rem))
    except (ValueError, TypeError):
        return range(0)


@register.filter
def replace(value, arg):
    """
    Replace substring:
    {{ text|replace:"old:new" }} or {{ phone|replace:" ":"" }}
    """
    if value is None:
        return ''
    val_str = str(value)
    arg_str = str(arg)
    if ':' in arg_str:
        old, new = arg_str.split(':', 1)
    else:
        old, new = arg_str, ''
    return val_str.replace(old, new)


@register.filter
def split(value, arg=','):
    """
    Split a string into a list:
    {% for item in text|split:',' %}
    """
    if not value:
        return []
    return [item.strip() for item in str(value).split(str(arg)) if item.strip()]


@register.filter
def repeat(value, count):
    """
    Repeat string:
    {{ '⭐'|repeat:5 }}
    """
    try:
        cnt = int(count)
        return str(value) * max(0, cnt)
    except (ValueError, TypeError):
        return str(value)


@register.filter
def filter_by(items, condition):
    """
    Filter an iterable or queryset by attribute/field value:
    {{ invitations|filter_by:'status=accepted' }}
    """
    if not items:
        return []
    
    cond_str = str(condition)
    if '=' in cond_str:
        key, val = cond_str.split('=', 1)
    elif ':' in cond_str:
        key, val = cond_str.split(':', 1)
    else:
        return items
    
    key = key.strip()
    val = val.strip().strip("'\"")
    
    # If Django QuerySet with filter support
    if hasattr(items, 'filter'):
        try:
            return items.filter(**{key: val})
        except Exception:
            pass
    
    result = []
    for item in items:
        item_val = getattr(item, key, None)
        if item_val is None and isinstance(item, dict):
            item_val = item.get(key)
        if str(item_val) == str(val):
            result.append(item)
    return result


@register.filter
def groupby(items, key):
    """
    Group items by a key or attribute:
    {% for group_key, group_items in items|groupby:"day_of_week" %}
    """
    if not items:
        return []
    
    def get_key(item):
        val = getattr(item, key, None)
        if val is None and isinstance(item, dict):
            val = item.get(key)
        return val

    # Sort items by key first for itertools.groupby
    try:
        sorted_items = sorted(list(items), key=lambda x: str(get_key(x) or ''))
        grouped = []
        for k, g in itertools.groupby(sorted_items, key=get_key):
            grouped.append((k, list(g)))
        return grouped
    except Exception:
        return []


@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def intcomma(value):
    """
    Format a number with comma as thousands separator:
    {{ 1000000|intcomma }} -> 1,000,000
    """
    if value is None:
        return '0'
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        try:
            return "{:,}".format(float(value))
        except (ValueError, TypeError):
            return str(value)


@register.filter
def contract_type_color(contract_type):
    """
    Return bootstrap color class for contract type
    """
    color_map = {
        'sale': 'success',
        'rent': 'info',
        'investment': 'warning',
        'other': 'secondary'
    }
    return color_map.get(contract_type, 'secondary')


@register.filter
def status_color(status):
    """
    Return bootstrap color class for contract status
    """
    color_map = {
        'draft': 'secondary',
        'pending': 'warning',
        'active': 'success',
        'completed': 'primary',
        'terminated': 'danger',
        'expired': 'danger',
        'cancelled': 'dark'
    }
    return color_map.get(status, 'secondary')


@register.filter
def days_remaining_color(days):
    """
    Return bootstrap color class based on days remaining
    """
    if days is None:
        return 'secondary'
    if days <= 0:
        return 'danger'
    if days <= 7:
        return 'danger'
    if days <= 30:
        return 'warning'
    return 'success'


@register.filter
def divide(value, arg):
    """
    Divide value by arg
    """
    try:
        if arg == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def default(value, arg):
    """
    Return value if it's truthy, else return arg
    """
    if value:
        return value
    return arg