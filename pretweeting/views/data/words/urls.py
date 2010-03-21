from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('pretweeting.views.data.words.views',
    # Example:
    
    (r'^compare/(.+)$', 'compare'),
    (r'^compare_chart_data/(.+)$', 'compare_chart_data'),
    
    (r'^random$', 'random'),
    (r'^search/(.+)$', 'search'),
    (r'^chart_data/(\d+)$', 'chart_data'),
    (r'^(\d+)$', 'show_word'),
    
    
    (r'^widget/word/(.+)$', 'widget_word'),
    (r'^widget/compare/(.+)$', 'widget_compare'),
)
