
import pexpect 
import re
import time, datetime
import sys, os
import urllib2, urllib
from utils import get_settings_file
from optparse import OptionParser
import logging
import traceback
import math

from django.utils.simplejson import loads
from django.core.management import setup_environ

URL_REGEX = re.compile(r'(http://|www\.)\S+')
EMAIL_REGEX = re.compile(r'\S+@\S+\.\w+', re.IGNORECASE)
WORD_REGEX = re.compile(r'[@#]?(?:\w+[\'-]\w+|\w+)', re.IGNORECASE)

MAX_WORD_LENGTH = 40
MIN_WORD_LENGTH = 2

VERY_BIG = 9999

# if this is set to false, it will process the same file over and over again.
REMOVE_FROM_BATCH_QUEUE = True

BATCHES_SUBDIR = 'batches'
LOCK_SUBDIR = 'lock'

RESTRICT_TIMEZONES = True
ALLOWED_TIMEZONES = [
    "Alaska",
    "Hawaii",
    "Arizona",
    "Indiana (East)",
    "Pacific Time (US & Canada)",
    "Mountain Time (US & Canada)",
    "Central Time (US & Canada)",
    "Eastern Time (US & Canada)"
]

def log_msg(msg):
    print msg
    logging.debug(msg)

def get_file():
    "Get the earliest file to process"
    available = pexpect.run("ls -rt %s" % BATCH_DIR)
    available = available.strip()
    if not available:
        return None
    else:
        return re.split(r'\s+', available)[0]

def process_word(word):
    return word.lower()

def process_text(text):
    
    # get all urls, but ignore them right now
    urls = re.findall(URL_REGEX, text, re.IGNORECASE)
    emails = re.findall(EMAIL_REGEX, text, re.IGNORECASE)
    
    # eliminate urls
    text = re.sub(URL_REGEX, '', text)
    text = re.sub(EMAIL_REGEX, '', text)
    text = text.strip()

    # separate words
    words = re.findall(WORD_REGEX, text)    
    words = [process_word(word) 
            for word in words
            if len(word) >= MIN_WORD_LENGTH 
            and len(word) <= MAX_WORD_LENGTH]
    
    # eliminate duplicates
    words = list(set(words))
    
    return words

def update_frequencies(frequencies, word_list):
    # words must be unique
    for word in word_list:
        if word not in frequencies:
            frequencies[word] = 0
        
        frequencies[word] += 1
        
def process_batch(file_name):
    "Lock the file and process it."
    
    timestamp = int(file_name.split('.')[0])
    
    log_msg('--- processing %s at %s ---' % (file_name, datetime.datetime.now().replace(microsecond=0)))
    pexpect.run("%s %s %s" % ('mv' if REMOVE_FROM_BATCH_QUEUE else 'cp',
            os.path.join(BATCH_DIR, file_name), LOCK_DIR))
    
    batch = open(os.path.join(LOCK_DIR, file_name))
    
    frequencies = {}
    
    total_lines = 0
    num_lines = 0
    num_words = 0
    
    t0 = time.time()
    while True:
        
        line = batch.readline()
        if not line:
            break
        try:
            data_object = loads(line)
        except ValueError:
            # if it's invalid json, just pass it
            continue
        
        total_lines += 1
        
        if RESTRICT_TIMEZONES:
            try:
                if data_object['user']['time_zone'] not in ALLOWED_TIMEZONES:
                    continue
            except KeyError:
                continue
        
        try:
            text = data_object['text']
        except KeyError:
            # not a status object
            continue
        
        num_lines += 1
           
        words = process_text(text)
        num_words += len(words)
        update_frequencies(frequencies, words)
    
    batch.close()
    
    # kill the file. no need to keep them
    os.remove(os.path.join(LOCK_DIR, file_name))
    
    total_words = len(frequencies.keys())
    total_count = sum(frequencies.values())
    t1 = time.time()
    log_msg('%d lines (of %d), %d words, %d usages counted: %.01fs.' % (
            num_lines, total_lines,
            total_words, total_count, 
            (t1-t0)))
    
    if total_words == 0:
        log_msg("skipping new batch...no content.")
        return
        
    # create new counts and measures
    new_batch = Batch.objects.create(
            total_messages=num_lines,
            created_on=datetime.datetime.fromtimestamp(timestamp))
    
    num_words = Word.objects.all().count()
    num_counts = Count.objects.all().count()
    
    # Bulk insert all words, ignoring errors
    for content, number in frequencies.iteritems():
        Word.objects.bulk_insert(content=content, send_pre_save=False)

    Word.objects.bulk_insert_commit(send_post_save=False,
            recover_pks=False)
    
    # Fetch the ids for new words so we can match them to counts
    words = Word.objects.filter(content__in=frequencies.keys())
    word_ids = dict([(word.content, word.id) for word in words])
        
    t2 = time.time()
    new_num_words = Word.objects.all().count()
    log_msg('%d new words created: %.01fs.' % (
            (new_num_words - num_words),
            (t2 - t1)))
    
    # And bulk insert the new counts
    for content, number in frequencies.iteritems():
        if content not in word_ids:
            # for some reason, the word wasn't successfully created by the 
            # bulk insert
            new_word = Word.objects.create(content=content)
            word_ids[content] = new_word.id
            log_msg("*** failsafe create for '%s'." % content)
        
        Count.objects.bulk_insert(
                word=word_ids[content],
                batch=new_batch, number=number, send_pre_save=False)
        
    Count.objects.bulk_insert_commit(send_post_save=False,
            recover_pks=False)
    
    new_num_counts = Count.objects.all().count()
    
    t3 = time.time()

    log_msg('%d new counts created: %.01fs.' % (
            (new_num_counts - num_counts),
            (t3 - t2)))
    
    # update round
    if Round.objects.count() > 0:
        t0 = time.time()
        
        maturations = []
        
        latest_round = Round.objects.latest()
        holdings = (Holding.objects
                .filter(user_round__is_active=True)
                .exclude(quantity=0)
                .select_related('word'))
        for holding in holdings:
            try:
                number = frequencies[holding.word.content]
            except KeyError:
                number = 0
            price = compute_price(number, new_batch.total_messages)
            holding.current_value = price * holding.quantity
            holding.save()
        
        user_rounds = UserRound.objects.filter(is_active=True)
        # aggregate into current value
        for user_round in user_rounds:
            user_round.update_current_value()
        
        t1 = time.time()

        log_msg('%d holdings and %d user rounds updated: %.01fs.' % (
                Holding.objects.count(), len(user_rounds),
                (t1 - t0)))
        
    # activate new measure
    new_batch.active = True
    new_batch.save()
    
    # update rounds.
    try:
        last_round = Round.objects.latest()
        last_number = last_round.number
        last_ends = last_round.ends_on
    except Round.DoesNotExist:
        last_round = None
        last_number = 0
        last_ends = datetime.datetime.now()
    
    if datetime.datetime.now() >= last_ends:
        
        if last_round:
            # tweet win
            if settings.TWEET_WIN:
                try:
                    winning_userround = (last_round.userround_set
                            .order_by('-current_value'))[0]
                except IndexError:
                    # no winner
                    pass
                else:                
                    message = "Congrats to @%s for winning %s with $%s! #pretweeting" % (
                        winning_userround.user.username,
                        last_round.name,
                        priceformat.currency(winning_userround.current_value))
                
                    access_token = settings.TWITTER_OAUTH_TOKEN
                    token = oauth.OAuthToken.from_string(access_token)
                    try:
                        post_tweet(CONSUMER, CONNECTION, token, message)
                    except TwitterError, e:
                        log_msg(e)
        
            # create frozen copies of all user rounds
            for user_round in last_round.userround_set.filter(is_active=True, is_frozen=False):
                user_round.copy_frozen()
                
        
        # create next round
        new_number = last_number + 1
        new_name = 'Round %d' % new_number
        new_round = Round(number=new_number, name=new_name)
        new_round.started_on = datetime.datetime.now()
        new_round.ends_on = datetime.datetime.now() + settings.ROUND_LENGTH
        new_round.save()

    # reset all slots
    cursor = connection.cursor()
    cursor.execute("UPDATE %s SET slots = 1 WHERE slots > 1" % Word._meta.db_table)
    transaction.commit_unless_managed()
    
    # and now count popularity and slots
    t0 = time.time()
    now = datetime.datetime.now()
    threshold = now - consts.POPULARITY_LOOKBACK
    
    unit_seconds_by_word_id = {}

    # count everything
    # count past histories
    histories = (HoldingHistory.objects
            .exclude(quantity=0)
            .filter(history_end__gte=threshold)
            .select_related('holding'))
    for history in histories:
        
        # print "History:", history.holding.word, history.quantity
        
        h0 = max(threshold, history.history_begin)
        h1 = history.history_end
        secs = total_seconds(h1 - h0)
        unit_seconds = secs * history.quantity
        if unit_seconds == 0:
            continue
        if history.holding.word_id not in unit_seconds_by_word_id:
            unit_seconds_by_word_id[history.holding.word_id] = 0
        unit_seconds_by_word_id[history.holding.word_id] += unit_seconds
        
    # count all holdings that 
    holdings = (Holding.objects
            .exclude(quantity=0)
            .filter(user_round__round__ends_on__gte=threshold)
            .select_related('user_round__round'))
    for holding in holdings:
        # holdings!
        # print "Holding:", holding.word, holding.quantity
        
        try:
            last_history = (holding.holdinghistory_set
                    .order_by('-history_end'))[0]
            h0 = last_history.history_end
        except IndexError:
            last_history = None
            h0 = holding.created_on
            
        if holding.user_round.round == last_round:
            # moves up to the current date
            h1 = now
        else:
            # ended at the last round
            h1 = holding.user_round.round.ends_on
        if h0 > h1:
            # error condition
            secs = 0
        else:
            secs = total_seconds(h1 - h0)
        unit_seconds = secs * holding.quantity
        if unit_seconds == 0:
            continue
        if holding.word_id not in unit_seconds_by_word_id:
            unit_seconds_by_word_id[holding.word_id] = 0
        unit_seconds_by_word_id[holding.word_id] += unit_seconds
    
    # debug print results, from least held to most
    words_by_time_held = sorted(unit_seconds_by_word_id.items(), 
            key=lambda (k, v): v)
    count_by_slots = [0] * (consts.TOP_WORD_SLOTS + 1)
    for i, (word_id, unit_seconds) in enumerate(words_by_time_held):
        rank = float(i + 1) / len(words_by_time_held)
        # should be 1 - consts.TOP_WORD_SLOTS
        slots = int(math.ceil(rank * consts.TOP_WORD_SLOTS))
        count_by_slots[slots] += 1
        # print Word.objects.get(id=word_id).content, unit_seconds, slots
        
        cursor.execute("UPDATE %s SET slots = %d WHERE id = %d" % (
                Word._meta.db_table, slots, word_id))
    transaction.commit_unless_managed()
    
    t1 = time.time()

    log_msg('%d words with slots [%s] updated: %.01fs.' % (
            len(words_by_time_held),
            ', '.join(['%dx%d' % (i + 1, count) 
                    for (i, count) in enumerate(count_by_slots[1:])]),
            (t1 - t0)))
            
def cleanup():
    now = datetime.datetime.now()
    a_week_ago = now - datetime.timedelta(days=7)
    latest_old_batch = (Batch.objects
            .filter(created_on__lt=a_week_ago)
            .order_by('-created_on'))[0]
    old_counts = Count.objects.filter(batch__lt=latest_old_batch.id)
    num_old_counts = old_counts.count()
    if not num_old_counts:
        return
    
    first_100 = old_counts[:100]
    for count in first_100:
        count.delete()
    log_msg('Cleanup found %d old counts, deleted %d.' % (
            num_old_counts, len(first_100)))
    
def main():
    
    waiting = False
    log_msg('starting process script at %s' %
            datetime.datetime.now().replace(microsecond=0))
    
    try:
        while True:            
            next_batch = get_file()
            if not next_batch:
                if not waiting:
                    log_msg('waiting...')
                time.sleep(1)
                waiting = True
            else:
                process_batch(next_batch)
                waiting = False
            cleanup()
                
    except KeyboardInterrupt:
        log_msg('...terminated.')
        sys.exit(0)
    except Exception:
        log_msg(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-s", "--settings", dest="settings",
                      help="choose which settings to use", metavar="SETTINGS")
    
    (options, args) = parser.parse_args()
    
    cwd = os.getcwd()
    sys.path.append(os.path.dirname(cwd))
    
    settings_option = options.settings or 'settings'
    settings_module = get_settings_file('../../pretweeting', settings_option)
    setup_environ(settings_module)
    from django.conf import settings
    from django.db.models import Sum
    from django.db import connection, transaction
    
    LOG_FILENAME = os.path.join(settings.LOCAL_DATA_DIR, 'process_log.txt')
    logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)
    
    BATCH_DIR = os.path.join(settings.LOCAL_DATA_DIR, BATCHES_SUBDIR)
    LOCK_DIR = os.path.join(settings.LOCAL_DATA_DIR, LOCK_SUBDIR)
    
    try: os.makedirs(LOCK_DIR)
    except OSError: pass
    try: os.makedirs(settings.BULK_INSERT_DIR)
    except OSError: pass
    
    from pretweeting import consts
    from pretweeting.apps.words.models import Word
    from pretweeting.apps.batches.models import (Count, Batch)
    from pretweeting.apps.rounds.models import Round
    from pretweeting.apps.users.models import Holding, HoldingHistory, UserRound
    from pretweeting.lib.timestamp import total_seconds
    from pretweeting.apps.batches.price import compute_price
    from pretweeting.apps.words.templatetags import priceformat
    
    from pretweeting.views.game.auth.utils import post_tweet, TwitterError, send_dm
    from pretweeting.views.game.auth import oauth
    from pretweeting.views.game.auth.views import CONSUMER, CONNECTION
    
    main()

