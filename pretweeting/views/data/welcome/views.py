
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
        return HttpResponseRedirect('/')
    
    return index(request, word)

def index(request, preload_word=None):
    
    try:
        latest_batch = Batch.objects.latest()
        now = latest_batch.created_on
    except IndexError:
        return render_to_response('game/welcome/nobatches.html', {
        }, context_instance=RequestContext(request))
    
    return render_to_response('data/welcome/index.html', {
        'latest_batch': latest_batch,
        'preload_word': preload_word,
        'game_url': settings.GAME_URL,
    }, context_instance=RequestContext(request))