import datetime

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_cookie
from django.core.cache import cache

from pretweeting import consts
from pretweeting.apps.rounds.models import Round

def help(request):
    
    latest_round = Round.objects.latest()
    return render_to_response('game/info/_help.html', {
        'latest_round': latest_round,
        'max_slots': consts.MAX_SLOTS,
        'top_slots': consts.TOP_WORD_SLOTS,
        'commission': int(100 * consts.COMMISSION),
        'min_buy_price': consts.MIN_BUY_PRICE,
    }, context_instance=RequestContext(request))