import datetime, time

def to_timestamp(dt):
  return int(time.mktime(dt.timetuple()))
  
def total_seconds(delta):
    return delta.seconds + 86400 * delta.days