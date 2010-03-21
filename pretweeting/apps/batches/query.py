import datetime, time

from django.conf import settings
from django.core.cache import cache

from pretweeting.consts import ALL_TWITTER_PRICE
from pretweeting.apps.words.models import Word
from pretweeting.apps.batches.models import Batch, Count
from pretweeting.apps.batches.price import compute_price

def aggregate_counts(batches, counts, start_at, aggregate_over=None):

    counts_by_batch = dict([(c.batch_id, c) for c in counts])

    batch_counts = []
    for batch in batches:
        if batch.id in counts_by_batch:
            batch_counts.append((batch, counts_by_batch[batch.id].number))
        else:
            batch_counts.append((batch, 0))
    
    values = [(batch.created_on, compute_price(number, batch.total_messages))
            for (batch, number) in batch_counts]
        
    return values