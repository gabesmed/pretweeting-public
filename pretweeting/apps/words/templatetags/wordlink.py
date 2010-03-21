from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def wordlink(word, length=0):
    url_sanitized = word.content.replace('#', '%23').replace('@', '%40')
    caption = word.content
    if len(caption) > length and length != 0:
        caption = '%s..' % caption[:length]
    
    link = "<a href='/w/%s' onclick='show_word(%d); return false;'>%s</a>" % (
            url_sanitized, word.id, caption)
    
    return mark_safe(link)


@register.simple_tag
def slots_tag(word):
    
    txt = ''.join(["&bull;"] * word.slots)
    span = '<span class="slots">%s</span>' % txt
    return mark_safe(span)