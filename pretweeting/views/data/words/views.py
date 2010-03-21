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
from pretweeting.views.data.charts import generate_word_chart, generate_word_charts
from pretweeting.consts import WORDS_PER_PAGE
from pretweeting.scripts.process import WORD_REGEX

# number of pages fwd and back from first page to show
LIST_PAGE_RANGE = 3
# interval at which to show all pages (1, 50, 100, 150, 154, 155, 156...)
MAJOR_INTERVAL = 20

def aggregate_counts(batches, counts, start_at, aggregate_over=None):

    counts_by_batch = dict([(c.batch_id, c) for c in counts])

    batch_counts = []
    for batch in batches:
        if batch.id in counts_by_batch:
            batch_counts.append((batch, counts_by_batch[batch.id].number))
        else:
            batch_counts.append((batch, 0))
    
    values = [(batch.created_on, float(number) / batch.total_messages)
            for (batch, number) in batch_counts]
        
    return values

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

    # .color0 { color: #a00; } .bg0 { background-color: #a00; }
    # .color1 { color: #0cf; } .bg1 { background-color: #0cf; }
    # .color2 { color: #f0c; } .bg2 { background-color: #f0c; }
    # .color3 { color: #fc0; } .bg3 { background-color: #fc0; }
    # .color4 { color: #8f8; } .bg4 { background-color: #8f8; }
    # 
colors = ["#aa0000", "#00ccff", "#ff00cc", "#ffcc00", "#88ff88"]

def compare_chart_data(request, content_list):

    content_list = content_list.split(',')
    words = []

    for content in content_list:
        content = content.lower()
        try:
            word = Word.objects.get(content=content)
            words.append(word)
        except Word.DoesNotExist:
            words.append(None)

    chart_length = 168
    average_over = datetime.timedelta(hours=1)

    now = Batch.objects.latest().created_on
    start = now - datetime.timedelta(hours=chart_length)

    earliest_time = start
    recent_batches = list(Batch.objects.active_after(earliest_time))
    earliest_batch = recent_batches[0]
    latest_batch = recent_batches[-1]
    
    value_lists = []
    
    for i, word in enumerate(words):
        if word is None: continue
        
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
        
        value_lists.append((values, colors[i]))

    chart = generate_word_charts(value_lists)
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
        return render_to_response('data/words/nodata.html', {
            'content': content
        }, context_instance=RequestContext(request))
        
    return HttpResponseRedirect('/words/%d' % word.id)

def show_word(request, word_id):
    
    word = get_object_or_404(Word, id=word_id)
    latest_batch = Batch.objects.latest()
    try:
        count = latest_batch.count_set.get(word=word)
        percent = 100 * float(count.number) / count.batch.total_messages
    except Count.DoesNotExist:
        count = None
        percent = 0
    
    link = 'http://%s/w/%s' % (settings.DATA_URL, word.content)
    
    iframe_url = 'http://%s/words/widget/word/%s' % (settings.DATA_URL, word.content)
    embed = '<iframe src="%s" width="410" height="400"></iframe>' % iframe_url
    return render_to_response('data/words/show.html', {
        'word': word,
        'percent': percent,
        'link': link,
        'embed': embed
    }, context_instance=RequestContext(request))

def widget_word(request, content):
    
    try:
        word = Word.objects.get(content=content)
    except Word.DoesNotExist:
        return render_to_response('data/words/nodata.html', {
            'content': content
        }, context_instance=RequestContext(request))
    
    latest_batch = Batch.objects.latest()
    try:
        count = latest_batch.count_set.get(word=word)
        percent = 100 * float(count.number) / count.batch.total_messages
    except Count.DoesNotExist:
        count = None
        percent = 0
    
    return render_to_response('data/words/widgets/show.html', {
        'word': word,
        'data_url': settings.DATA_URL,
        'percent': percent,
        'data_media_url': 'http://%s/static_media/' % settings.DATA_URL,
        'data_url': settings.DATA_URL
    }, context_instance=RequestContext(request))
    
def widget_compare(request, content):
    pass

def compare(request, content_list):
    
    words_errors = []

    for content in content_list.split(','):
        content = content.lower()
        try:
            word = Word.objects.get(content=content)
            words_errors.append((word, None))
        except Word.DoesNotExist:
            words_errors.append((None, "We have no data on '%s'" % content))
        
    return render_to_response('data/words/compare.html', {
        'words_errors': words_errors,
        'content_list': content_list
    }, context_instance=RequestContext(request))
    
    
    
    