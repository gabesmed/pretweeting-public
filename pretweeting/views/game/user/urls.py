from django.conf import settings
from django.conf.urls.defaults import *
from pretweeting.views.game.user import views

urlpatterns = patterns('pretweeting.views.game.user.views',
    (r'^portfolio$', views.portfolio),
    (r'^intro$', views.intro),
    
    url(r'^order$', views.order, name='order'),
    url(r'^chat$', views.chat, name='chat'),
    url(r'^reset$', views.reset, name='reset'),
)
