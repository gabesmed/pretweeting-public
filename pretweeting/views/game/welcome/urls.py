from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('pretweeting.views.game.welcome.views',
    # Example:
    (r'^$', 'index'),
    (r'^w/(.+)$', 'preload_word')
)
