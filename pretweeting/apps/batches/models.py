import datetime, time

from django.db import models
from django.conf import settings
from django.core.cache import cache

from pretweeting.apps.words.models import Word
from pretweeting.apps.managers import BulkInsert

LATEST_BATCH_KEY = 'pretweeting_latest_batch'

def get_active_after_key(start):
    return 'pretweting_active_after_%d' % time.mktime(start.timetuple())

class BatchManager(models.Manager):
    
    def active_after(self, start):
        if not settings.CACHE_LATEST_BATCH:
            return self._active_after(start)
        l = cache.get(get_active_after_key(start))
        if l is None:
            l = list(self._active_after(start))
            cache.set(get_active_after_key(start), l,
                    settings.CACHE_LATEST_BATCH_FOR)
        return l
        
    def _active_after(self, start):
        return self.filter(created_on__gt=start, active=True)
    
    def latest(self):
        if not settings.CACHE_LATEST_BATCH:
            return self._latest()
        l = cache.get(LATEST_BATCH_KEY)
        if l is None:
            l = self._latest()
            cache.set(LATEST_BATCH_KEY, l, settings.CACHE_LATEST_BATCH_FOR)
        return l
    
    def _latest(self): 
        return self.filter(active=True).order_by('-created_on')[0]

class Batch(models.Model):
    """
    A measure is taken after every new count, and sums up the total number
    of words over, say, the past day.
    """
    created_on = models.DateTimeField(db_index=True)
    total_messages = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=False)

    objects = BatchManager()

    class Meta:
        ordering = ('created_on',)
        get_latest_by = ('created_on',)

class Count(models.Model):
    """Important: each count can only be 65536 tweets, because the numbers
    can't exceed that for any count-indexed storage.
    """
    batch = models.ForeignKey(Batch)
    word = models.ForeignKey(Word)
    number = models.PositiveSmallIntegerField()

    objects = BulkInsert()
    