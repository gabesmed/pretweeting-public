from django import template

register = template.Library()

@register.filter
def escapehash(msg):
    return msg.replace('#', '%23').replace('@', '%40')
escapehash.is_safe = True
