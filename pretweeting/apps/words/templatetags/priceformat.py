from django import template

register = template.Library()

from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import floatformat

@register.filter
def floatcomma(value, arg=-1):
    
    try:
        value = float(value)
    except ValueError:
        return ""
    
    formatted = floatformat(value, arg)
    if '.' in formatted:
        return '%s.%s' % (intcomma(int(value)), formatted.split('.')[1])
    else:
        return intcomma(int(value))
floatcomma.is_safe = True

# when to show something as $123.4M instead of $123,456,789.01

MILLION = 1000000
BILLION = 1000 * MILLION
TRILLION = 1000 * BILLION

quantities = [(TRILLION, 'T'), (BILLION, 'B'), (MILLION, 'M')]

@register.filter
def quantity(value, places=0):
    
    for quantity, suffix in quantities:
        if value > quantity:
            try:
                in_units = float(value) / quantity
                return '%.1f%s' % (in_units, suffix)
            except ValueError:
                return ""
    if places == 0:
        return intcomma(value)
    else:
        return floatcomma(value, places)
    
quantity.is_safe = True
   
@register.filter
def currency(value):
    return quantity(value, 2)

floatcomma.is_safe = True

@register.filter
def plusminuspercent(value, decimal=-1):
    try:
        value = float(value)
    except ValueError:
        return ""
    
    rep = quantity(value, decimal)
    if value > 0:
        rep = '+%s' % rep
        
    if value > 0:
        css = 'up'
        prefix = '&#9650;'
    elif value < 0:
        css = 'down'
        prefix = '&#9660;'
    else:
        css = 'nochange'
        prefix = '&#9658;'
    
    full_rep = "<span class='%s'>%s&nbsp;%s%%</span>" % (
            css, prefix, rep)
    
    return full_rep
plusminuspercent.is_safe = True