import datetime
from random import randint

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_cookie
from django.core.cache import cache

from pretweeting.apps.users.models import UserRound
from pretweeting.apps.words.models import Word
from pretweeting.apps.batches.models import Batch
from pretweeting.apps.rounds.models import Round

def preload_word(request, content):
    try:
        word = Word.objects.get(content=content)
    except Word.DoesNotExist:
        word = None
    
    return index(request, word)

@vary_on_cookie
def index(request, preload_word=None):
    if request.user.username == 'admin':
        return HttpResponseRedirect('/administration')
        
    try:
        latest_batch = Batch.objects.latest()
        now = latest_batch.created_on
    except IndexError:
        return render_to_response('game/welcome/nobatches.html', {
        }, context_instance=RequestContext(request))
        
    latest_round = Round.objects.latest()
        
    return render_to_response('game/welcome/index.html', {
        'latest_batch': latest_batch,
        'latest_round': latest_round,
        'preload_word': preload_word,
        'data_url': settings.DATA_URL,
    }, context_instance=RequestContext(request))