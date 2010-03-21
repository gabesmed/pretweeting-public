from django import template

import pytz
import datetime

register = template.Library()

local_timezone_string = 'US/Pacific'

@register.filter(name='localtime')
def localtime(time):
  if time is None:
    return None
  if isinstance(time, basestring):
    return None
  
  utc_time = time.replace(tzinfo=pytz.utc)
  local_tz = pytz.timezone(local_timezone_string)
  local_time = utc_time.astimezone(local_tz)
  
  return local_time

localtime.is_safe = True