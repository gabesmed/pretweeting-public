from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^', include('pretweeting.views.game.welcome.urls')),
    (r'^words/', include('pretweeting.views.game.words.urls')),
    (r'^user/', include('pretweeting.views.game.user.urls')),
    (r'^stats/', include('pretweeting.views.game.stats.urls')),
    (r'^info/', include('pretweeting.views.game.info.urls')),
    (r'^auth/', include('pretweeting.views.game.auth.urls')),
    
    # Uncomment the next line to enable the admin:
    (r'^administration/(.*)', admin.site.root),
)

if settings.DEBUG:
	urlpatterns += patterns('',
	  (r'^static_media/(?P<path>.*)$',
	    'django.views.static.serve', {
	    'document_root': settings.MEDIA_ROOT }),
	)