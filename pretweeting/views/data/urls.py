from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    (r'^', include('pretweeting.views.data.welcome.urls')),
    (r'^words/', include('pretweeting.views.data.words.urls')),
)

if settings.DEBUG:
	urlpatterns += patterns('',
	  (r'^static_media/(?P<path>.*)$',
	    'django.views.static.serve', {
	    'document_root': settings.MEDIA_ROOT }),
	)