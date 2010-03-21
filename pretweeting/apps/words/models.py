import datetime
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from pretweeting import consts
from pretweeting.lib.timestamp import total_seconds
from pretweeting.apps.managers import BulkInsert
  
class Word(models.Model):
    
    content = models.CharField(max_length=40, db_index=True, unique=True)
    slots = models.PositiveSmallIntegerField(db_index=True, default=1)
    
    objects = BulkInsert()
        
    def get_absolute_url(self):
        return '/words/%s' % self.content
    
    def latest_price(self, force=False):
        if force or not hasattr(self, '_latest_price'):
            self._load_latest_price()
        return self._latest_price
    
    def latest_count(self, force=False):
        if force or not hasattr(self, '_latest_count'):
            self._load_latest_price()
        return self._latest_count
    
    def _load_latest_price(self):
        from pretweeting.apps.batches.models import Batch, Count
        from pretweeting.apps.batches.price import get_price
        latest_batch = Batch.objects.latest()

        try:
            count = latest_batch.count_set.get(word=self)
            price = get_price(count, latest_batch)
        except Count.DoesNotExist:
            count = Count(word=self, batch=latest_batch, number=0)
            price = get_price(count, latest_batch)

        self._latest_price = price
        self._latest_count = count.number
            
    def __unicode__(self):
        return self.content
    
    class Meta:
        ordering = ('content',)