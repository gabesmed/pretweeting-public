from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('pretweeting.views.data.welcome.views',
    # Example:
    (r'^$', 'index'),
    (r'^w/(.+)$', 'preload_word')
)