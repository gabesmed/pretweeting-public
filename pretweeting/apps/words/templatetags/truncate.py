from django import template

register = template.Library()

@register.filter(name='truncate')
def truncate(msg, length):
    if len(msg) <= length:
        return msg
    else:
        return '%s..' % msg[:length]