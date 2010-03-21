import datetime
import urllib, urllib2

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_cookie
from django.core.cache import cache
from django.db.models import Sum, Q
from django.utils.simplejson import loads

from pretweeting import consts
from pretweeting.apps.words.models import Word
from pretweeting.apps.batches.models import Batch, Count
from pretweeting.apps.rounds.models import Round
from pretweeting.apps.users.models import UserRound, Holding, Order

TIMES_URL = "http://api.nytimes.com/svc/news/v2/all/last24hours?limit=8&api-key=8c2f9b114cf72f0dfa76d871370b6745:6:9180396"
TWITTER_URL = "http://search.twitter.com/trends/current.json"
NUM_TRIES = 2

def trends(request):
    
    def load_data(url):
        for trynumber in xrange(NUM_TRIES):
            try:
                req = urllib2.Request(url=url)
                f = urllib2.urlopen(req)
                data = loads(f.read())
                return data
            except urllib2.URLError:
                pass
        return []
    
    times_data = load_data(TIMES_URL)
    times_trends = [(result['headline'], result['summary'])
            for result in times_data['results']]
    
    twitter_data = load_data(TWITTER_URL)
    twitter_trends = []
    for time, trends in twitter_data['trends'].iteritems():
        for trend in trends:
            twitter_trends.append(trend['name'])
    
    latest_round = Round.objects.latest()

    start_threshold = datetime.datetime.now() - datetime.timedelta(days=1)

    latest_words = (Word.objects
            .filter(order__user_round__round=latest_round,
                    order__created_on__gt=start_threshold)
            .annotate(quantity_orders=Sum('order__quantity'))
            .order_by('-quantity_orders'))[:20]
    latest_words = sorted(latest_words, key=lambda w: w.content)
        
    return render_to_response('game/stats/_trends.html', {
        'times_trends': times_trends,
        'twitter_trends': twitter_trends,
        'latest_words': latest_words
    }, context_instance=RequestContext(request))

def leaderboard(request):
    
    latest_round = Round.objects.latest()
    previous_round = (Round.objects
            .filter(number__lt=latest_round.number)
            .order_by('-number'))[0]
    
    threshold = datetime.datetime.now() - datetime.timedelta(days=7)
    user_rounds = (latest_round.userround_set
            .order_by('-current_value', 'user__username')
            .filter(last_trade__gt=threshold)
            .select_related('user')
            .select_related('round'))[:40]
    
    user_rounds = [(user_round, user_round.user.frozen_at(previous_round))
            for user_round in user_rounds]
    
    before_long_round = Q(round__number__gte=8, round__number__lt=24, is_frozen=True)
    in_long_round = Q(is_frozen=False, round__number=24)
    is_relevant = before_long_round | in_long_round
    
    all_time_winners = (UserRound.objects
            .order_by('-current_value', 'user__username')
            .filter(is_relevant)
            .select_related('user')
            .select_related('round'))
    # all_time_winners = all_time_winners[:10]
    all_time_winners = all_time_winners[:40]
    
    w = []
    w_names = set()
    for x in all_time_winners:
        if x.user.username not in w_names:
            w.append(x)
            w_names.add(x.user.username)
    all_time_winners = w[:20]
    
    return render_to_response('game/stats/_leaderboard.html', {
        'user_rounds': user_rounds,
        'latest_round': latest_round,
        'all_time_winners': all_time_winners
    }, context_instance=RequestContext(request))
    