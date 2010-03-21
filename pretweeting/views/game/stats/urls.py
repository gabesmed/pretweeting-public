from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('pretweeting.views.game.stats.views',
    (r'^leaderboard$', 'leaderboard'),
    (r'^trends$', 'trends'),
)
