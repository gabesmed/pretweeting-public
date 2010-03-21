from django.conf.urls.defaults import *

from pretweeting.views.game.auth.views import *

urlpatterns = patterns('pretweeting.views.game.auth.views',    
    url(r'^auth/$',
        view=auth,
        name='twitter_oauth_auth'),

    url(r'^return/$',
        view=return_,
        name='twitter_oauth_return'),
    
    url(r'^clear/$',
        view=unauth,
        name='twitter_oauth_unauth'),
)
