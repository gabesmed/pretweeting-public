import datetime
import time
import math

from django.utils.simplejson import dumps
from django.utils.timesince import timesince

from pretweeting import consts
from pretweeting.apps.words.templatetags.timezone import localtime

from pretweeting.lib.pyofc2 import *

BACKGROUND_COLOR = "#ffffff"
LIGHT_LINE_COLOR = "#dddddd"
MAIN_LINE_COLOR = "#444444"

def to_timestamp(dt):
  return int(time.mktime(dt.timetuple()))

def to_hour(dt, start):
    return float(to_timestamp(dt) - to_timestamp(start)) / 60 / 60
 
def get_scatter_values(values, start, color):
    
    s = scatter_line(colour=color, dot_size=1)

    scatter_values = []
    for created_on, price in values:
        x = to_hour(created_on, start)
        y = price
        tip = '%s: %0.2f%%' % (localtime(created_on).strftime('%a, %I:%M%p').lower(), 
                price)
        scatter_values.append(scatter_value(x=x, y=y, tip=tip))
    
    s.values = scatter_values
    
    return s

def generate_word_charts(value_lists):
    
    chart = open_flash_chart(bg_colour=BACKGROUND_COLOR)
    
    max_price = max([max([m[1] for m in values]) 
            for (values, color) in value_lists]) * 100
    
    start = value_lists[0][0][0][0]
    end = value_lists[0][0][-1][0]
    
    for values, color in value_lists:
        values = [(d, v*100) for (d,v) in values]
        main_plot = get_scatter_values(values, start, color=color)
        chart.add_element(main_plot)

    # 7 hour chart
    hour_span = to_hour(end, start)
    steps = 24

    labels = []
    for h in range(0, int(math.ceil(hour_span)), steps):
        # print h
        s = start + datetime.timedelta(hours=h)
        text = localtime(s).strftime('%I:%M%p')
        labels.append('')

    xaxis = x_axis()
    xaxis.min = 0
    xaxis.max = hour_span
    xaxis.offset = False
    xaxis.steps = steps
    xaxis.labels = {'labels': labels, 'steps': steps }
    xaxis.colour = LIGHT_LINE_COLOR
    xaxis.grid_colour = LIGHT_LINE_COLOR

    chart.x_axis = xaxis

    yaxis = y_axis()
    yaxis.min = 0
    yaxis.max = max_price * 1.25

    steps = max_price / 10
    yaxis.steps = steps
    yaxis.labels = None
    yaxis.colour = LIGHT_LINE_COLOR
    yaxis.grid_colour = LIGHT_LINE_COLOR
    chart.y_axis = yaxis
    chart['num_decimals'] = 2
    chart['is_fixed_num_decimals_forced'] = True
    return chart.render()
    
def generate_word_chart(values):
    
    values = [(d, v*100) for (d,v) in values]
    start = values[0][0]
    end = values[-1][0]
    max_price = max([m[1] for m in values])
    
    chart = open_flash_chart(bg_colour=BACKGROUND_COLOR)

    main_plot = get_scatter_values(values, start, color=MAIN_LINE_COLOR)
    chart.add_element(main_plot)
    
    # 7 hour chart
    hour_span = to_hour(end, start)
    steps = 24
    
    labels = []
    for h in range(0, int(math.ceil(hour_span)), steps):
        # print h
        s = start + datetime.timedelta(hours=h)
        text = localtime(s).strftime('%I:%M%p')
        labels.append('')
    
    xaxis = x_axis()
    xaxis.min = 0
    xaxis.max = hour_span
    xaxis.offset = False
    xaxis.steps = steps
    xaxis.labels = {'labels': labels, 'steps': steps }
    xaxis.colour = LIGHT_LINE_COLOR
    xaxis.grid_colour = LIGHT_LINE_COLOR
    
    chart.x_axis = xaxis
    
    yaxis = y_axis()
    yaxis.min = 0
    yaxis.max = max_price * 1.25
    
    steps = max_price / 10
    yaxis.steps = steps
    yaxis.labels = None
    yaxis.colour = LIGHT_LINE_COLOR
    yaxis.grid_colour = LIGHT_LINE_COLOR
    chart.y_axis = yaxis
    chart['num_decimals'] = 2
    chart['is_fixed_num_decimals_forced'] = True
    return chart.render()
