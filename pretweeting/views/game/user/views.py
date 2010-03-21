import datetime
from random import randint

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_cookie
from django.core.cache import cache
from django.utils.simplejson import dumps
from django.db.models import Sum
from django.db.models import Q

from djangodblog import DBLogMiddleware

from pretweeting import consts
from pretweeting.apps.words.models import Word
from pretweeting.apps.batches.models import Batch, Count
from pretweeting.apps.rounds.models import Round
from pretweeting.apps.users.models import UserRound, Holding, Order, OrderError
from pretweeting.apps.batches.price import get_price
from pretweeting.apps.words.templatetags import priceformat

from pretweeting.views.game.auth.utils import post_tweet, TwitterError
from pretweeting.views.game.auth import oauth
from pretweeting.views.game.auth.views import CONSUMER, CONNECTION

def get_interesting_words_and_prices():
    latest_batch = Batch.objects.latest()
    key = 'batch_interesting_words_%d' % latest_batch.id
    words_and_prices = cache.get(key)
    if words_and_prices is None:   
        counts = (latest_batch.count_set.order_by('-number')
                .select_related('word'))[280:700]
        words_and_prices = [(count.word, get_price(count, latest_batch))
                for count in counts]
        cache.set(key, words_and_prices, 60 * 60 * 24)
    return words_and_prices

def suggest_words_and_prices(num):
    interesting_words = get_interesting_words_and_prices()
    try:
        return [interesting_words[randint(0, len(interesting_words) - 1)]
                for i in xrange(num)]
    except ValueError:
        return []
        

@never_cache
def portfolio(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/user/intro')
    
    latest_batch = Batch.objects.latest()
    latest_round = Round.objects.latest()
    
    user_round = request.user.get_active_user_round()
    holdings = user_round.holding_set.exclude(quantity=0).order_by('word__content')
        
    previous_rounds = (request.user.userround_set
            .filter(round__lt=user_round.round_id)
            .order_by('round'))[:5]
    
    suggested_word_prices = suggest_words_and_prices(12)
        
    return render_to_response('game/user/_portfolio.html', {
        'in_current_round': user_round.round == latest_round,
        'latest_round': latest_round,
        'latest_batch': latest_batch,
        'holdings': holdings,
        'user_round': user_round,
        'rank': user_round.rank(),
        'now': datetime.datetime.now(),
        'previous_rounds': previous_rounds,
        'suggested_word_prices': suggested_word_prices
    }, context_instance=RequestContext(request))

def intro(request):
    "For unauthenticated users"
    latest_round = Round.objects.latest()
    cash = latest_round.starting_cash
    
    suggested_word_prices = suggest_words_and_prices(12)
    
    return render_to_response('game/user/_intro.html', {
        'cash': cash,
        'suggested_word_prices': suggested_word_prices
    }, context_instance=RequestContext(request))

def chat(request):
    
    if request.method == 'POST':
        
        message = request.POST['message']
        if not message:
            return HttpResponse(dumps({
                'success': False,
                'error': 'You need a message to send!'
            }))
        
        if len(message) > 140 - len(' #pretweeting'):
            return HttpResponse(dumps({
                'success': False,
                'error': 'Message too long'
            }))
        
        access_token = request.session.get('access_token', None)
        if access_token is None:
            access_token = request.user.get_profile().access_token
        if access_token is None:
             return HttpResponse(dumps({
                 'success': False,
                 'error': 'Invalid authentication'
             }))
        
        token = oauth.OAuthToken.from_string(access_token)

        if not settings.POST_TWEETS or not access_token:
            return HttpResponse(dumps({
                'success': False,
                'error': "Can't post to twitter."
            }))
        
        full_msg = '%s #pretweeting' % message
        try:
            response = post_tweet(CONSUMER, CONNECTION, token, full_msg)
        except TwitterError, e:
            return HttpResponse(dumps({
                'success': False,
                'error': 'Error posting to twitter.'
            }))
        else:
            return HttpResponse(dumps({
                'success': True,
                'message': 'Sent! Wait few seconds for it to show up.'
            }))
    
    return render_to_response('game/user/_chat.html', {
    }, context_instance=RequestContext(request))

@login_required
def reset(request):
    
    latest_round = Round.objects.latest()
    user_round = request.user.get_active_user_round()
    if user_round.round == latest_round:
        user_round.reset()
        request.session['notice'] = 'Portfolio reset!'
    else:
        user_round = request.user.new_user_round()
        request.session['notice'] = 'New portfolio created!'
    
    return HttpResponseRedirect('/')

AUTO_DISABLE_TWEETING_AT = 3

@login_required
def order(request):
    
    latest_batch = Batch.objects.latest()
    latest_round = Round.objects.latest()
    
    user_round = request.user.get_active_user_round()
    profile = request.user.get_profile()
    
    word_id = request.POST['word_id'] # word text
    order_type = request.POST.get('order', '').upper() # 'B' or 'S'
    if order_type not in ['B', 'S']:
        return HttpResponseBadRequest("Invalid order type")
    
    if request.POST.get('tweet', None) in ['on', '1']:
        tweet = True
    elif request.POST.get('tweet', '') in ['', '0']:
        tweet = False
    else:
        tweet = profile.tweets_ok
    
    # update preference for tweeting
    if tweet != profile.tweets_ok:
        profile.tweets_ok = tweet
        profile.save()
    
    tweet_order = (settings.POST_TWEETS and tweet)
    
    try:
        word = Word.objects.get(id=word_id)
    except Word.DoesNotExist:
        return HttpResponseBadRequest("Word not found")
        
    try:
        if order_type == 'B':
            quantity = int(request.POST.get('quantity',0) or 0)
            new_order = user_round.buy(word, quantity, tweeted=tweet_order)
        elif order_type == 'S':
            quantity = int(request.POST.get('quantity', 0) or 0) # a number
            new_order = user_round.sell(word, quantity, tweeted=tweet_order)
            
    except OrderError, e:
        DBLogMiddleware().process_exception(request, e)
        return HttpResponseBadRequest(str(e))
  
    # block for all users but me
    if tweet_order:
        new_order.tweet(profile.access_token)
    
    from pretweeting.views.game.words.views import show_word
    return HttpResponse(dumps({
        'message': new_order.confirmation,
        'portfolio': portfolio(request).content,
        'word': show_word(request, word.id).content
    }))