from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('pretweeting.views.game.words.views',
    # Example:
    (r'^$', 'list_words'),
    (r'^page/(\d+)$', 'list_words'),
    
    (r'^random$', 'random'),
    (r'^search/(.+)$', 'search'),
    (r'^chart_data/(\d+)$', 'chart_data'),
    (r'^(\d+)$', 'show_word'),
    
)
