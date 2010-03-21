import datetime
import re
import math
from random import randint

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404, Http404
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.decorators.cache import never_cache
from django.utils.simplejson import dumps
from django.db.models import Sum

from pretweeting.lib.stopwords import stop_words
from pretweeting import consts
from pretweeting.apps.batches.price import get_price
from pretweeting.apps.words.models import Word
from pretweeting.apps.rounds.models import Round
from pretweeting.apps.users.models import UserRound, Holding
from pretweeting.apps.batches.models import Batch, Count
from pretweeting.apps.batches.query import aggregate_counts
from pretweeting.apps.words.templatetags import priceformat
from pretweeting.views.game.charts import generate_word_chart
from pretweeting.consts import WORDS_PER_PAGE
from pretweeting.scripts.process import WORD_REGEX

# number of pages fwd and back from first page to show
LIST_PAGE_RANGE = 3
# interval at which to show all pages (1, 50, 100, 150, 154, 155, 156...)
MAJOR_INTERVAL = 20

def chart_data(request, word_id):
    chart_length = 168
    average_over = datetime.timedelta(hours=1)
    word = get_object_or_404(Word, id=word_id)
        
    now = Batch.objects.latest().created_on
    start = now - datetime.timedelta(hours=chart_length)
    
    earliest_time = start
    recent_batches = list(Batch.objects.active_after(earliest_time))
    earliest_batch = recent_batches[0]
    latest_batch = recent_batches[-1]
    counts = Count.objects.filter(word=word)
    counts = counts.filter(batch__id__gte=earliest_batch.id)
    # counts = counts.order_by('id')
    counts = list(counts)
    values = aggregate_counts(recent_batches, counts, start)
    sums = []
    for dt, number in values:
        if len(sums) > 0 and dt < sums[-1][0] + average_over:
            sums[-1][1] += number
            sums[-1][2] += 1
        else:
            sums.append([dt, number, 1])
    
    if values[-1][0] != sums[-1][0]:
        sums.append([values[-1][0], values[-1][1], 1])
    
    values = [(dt, float(total) / float(count)) 
            for (dt, total, count) in sums]
        
    chart = generate_word_chart(values)
    return HttpResponse(chart)

def random(request):
    latest_batch = Batch.objects.latest()
    try:
        random_count = (latest_batch.count_set.order_by('-number')
                .select_related('word')[randint(280, 700)])
        random_word = random_count.word
    except IndexError:
        return HttpResponse('') # no word
    
    return HttpResponseRedirect('/words/%d' % random_word.id)

def search(request, content):
    content = content.replace('!', '\'')
    try:
        word = Word.objects.get(content=content)
    except Word.DoesNotExist:
        return render_to_response('game/words/nodata.html', {
            'content': content
        }, context_instance=RequestContext(request))
        
    return HttpResponseRedirect('/words/%d' % word.id)

@never_cache
def show_word(request, word_id):
    
    word = get_object_or_404(Word, id=word_id)
    price = word.latest_price()
    latest_round = Round.objects.latest()
    
    buy_price = max(price, consts.MIN_BUY_PRICE)
    
    # See if the user is authenticated or not
    if request.user.is_authenticated():
        tweets_ok = request.user.get_profile().tweets_ok
        user_round = request.user.get_active_user_round()
    else:
        user_round = None
        tweets_ok = True

    # generate starting cash if it's existent.
    if user_round:
        cash = user_round.cash
        slots_held = user_round.slots_held()
        try:
            holding = (user_round.holding_set
                    .filter(word=word)
                    .exclude(quantity=0))[0]
        except IndexError:
            holding = None
        try:
            last_order = user_round.order_set.order_by('-created_on')[0]
        except IndexError:
            last_order = None
    else:
        holding = None
        last_order = None
        cash = latest_round.starting_cash
        slots_held = 0
    
    qty_held = holding.quantity if holding else 0
    forbidden = None
    
    slots_available = consts.MAX_SLOTS - slots_held
    
    qty_available = slots_available // word.slots
    
    if slots_available <= 0:
        forbidden = "You can't buy any more words because you've already filled \
%d slots. You'll have to sell some of your portfolio before you buy \
new words." % consts.MAX_SLOTS
    elif slots_available < word.slots:
        forbidden = "You can't buy this word because you only have %d slots \
available, and this word requires %d. You'll have to sell some of your \
portfolio before you buy new words." % (slots_available, word.slots)
            
    sell_units = []
    sell_price = price * (1 - consts.COMMISSION)
    if qty_held >= 1:
        sell_units.append(('all', qty_held, qty_held * sell_price))
    if qty_held >= 2:
        sell_units.append(('half', int(qty_held / 2), int(qty_held / 2) * sell_price))
    if qty_held >= 8:
        sell_units.append(('a quarter', int(qty_held / 4), int(qty_held / 4) * sell_price))
    
    buy_message = None
    if buy_price > price:
        buy_message = "You can buy this word at the minimum buy price of $%s." % (
                priceformat.currency(consts.MIN_BUY_PRICE))
    
    if buy_price == 0:
        forbidden = "You can't buy this word right now because we have no \
data on its current frequency of usage."
        qty_afford = 0
    else:
        c = word.latest_count()
        if word.latest_count() < consts.MIN_NUMBER_TO_BUY:
            forbidden = "You can't buy this word right now because the price \
is too low for us to provide accurate data."
            qty_afford = 0
        else:
            qty_afford = int(cash / buy_price)
            if qty_afford == 0:
                forbidden = "You can't afford to buy any shares of this word."

    if forbidden:
        buy_units = []
    else:
        def units(total):
            yield total
            if total > 1:
                yield total / 2
                for unit in units(total / 10):
                    yield unit
        buy_units = units(consts.MAX_SLOTS)
        qty_possible = min(qty_afford, qty_available)
        buy_units = filter(lambda u: u <= qty_possible, buy_units)
        if not buy_units or buy_units[0] != qty_possible:
            buy_units.insert(0, qty_possible)
        buy_units = [(unit, buy_price * unit, word.slots * unit)
                for unit in buy_units[:4]]
    
    return render_to_response('game/words/show.html', {
        'word': word,
        'price': price,
        'buy_message': buy_message,
        'holding': holding,
        'forbidden': forbidden,
        'buy_units': buy_units,
        'sell_units': sell_units,
        'commission_percent': int(100 * consts.COMMISSION),
        'qty_held': qty_held,
        'qty_afford': qty_afford,
        'cash': cash,
        'tweets_ok': tweets_ok,
        'slots_available': slots_available,
        'slots_maximum': consts.MAX_SLOTS,
        'limiter': 'cash' if qty_afford < qty_available else 'slots'
    }, context_instance=RequestContext(request))

def list_words(request, page_num=1):
    batch = Batch.objects.latest()
    counts = (batch.count_set
            .order_by('-number')
            .filter(number__gte=consts.MIN_NUMBER_TO_SHOW)
            .select_related('word'))
    
    paginator = Paginator(counts, WORDS_PER_PAGE)
    page_num = int(page_num)
    try:
        page = paginator.page(page_num)
    except (EmptyPage, InvalidPage):
        page_num = paginator.num_pages
        page = paginator.page(page_num)
    
    prev_pages, next_pages, show_first, show_last = pagination_help(
            page_num, paginator, LIST_PAGE_RANGE)
    
    word_prices = [(count.word, get_price(count, batch))
            for count in page.object_list]
    
    return render_to_response('game/words/list.html', {
        'show_first': show_first,
        'show_last': show_last,
        'prev_pages': prev_pages,
        'next_pages': next_pages,
        'page': page,
        'page_subpath': 'page',
        'word_prices': word_prices
    }, context_instance=RequestContext(request))

def pagination_help(page_num, paginator, page_range):
    num_before = page_range
    num_after = page_range
    if page_num <= page_range:
        # cut back before
        num_before = page_num - 1
        num_after = min(2 * page_range - num_before, 
                paginator.num_pages - page_num)
    elif page_num > paginator.num_pages - page_range:
        num_after = paginator.num_pages - page_num
        num_before = min(2 * page_range - num_after,
                page_num - 1)
    
    prev_pages = range(page_num - num_before, page_num)
    next_pages = range(page_num + 1, page_num + num_after + 1)
    show_first = show_last = []
    if prev_pages and prev_pages[0] > 1:
        show_first = [1]
        show_first.extend(range(MAJOR_INTERVAL, prev_pages[0], MAJOR_INTERVAL))
    if next_pages and next_pages[-1] < paginator.num_pages:
        show_last = range(((next_pages[-1] // MAJOR_INTERVAL) + 1) * MAJOR_INTERVAL, 
                paginator.num_pages + 1, MAJOR_INTERVAL)
        if not show_last or show_last[-1] != paginator.num_pages:
            show_last.append(paginator.num_pages)
    
    return prev_pages, next_pages, show_first, show_last
    