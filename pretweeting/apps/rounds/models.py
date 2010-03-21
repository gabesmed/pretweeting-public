from django.db import models

class Round(models.Model):
    """
    A game round
    """
    started_on = models.DateTimeField()
    ends_on = models.DateTimeField()
    number = models.IntegerField()
    name = models.CharField(max_length=32)
    
    starting_cash = models.IntegerField(default=5000)
    
    class Meta:
        get_latest_by = ('started_on', )
        ordering = ('-started_on',)
    
    def __unicode__(self):
        return self.name
    
    def num_players(self):
        return self.userround_set.filter(is_frozen=False).count()
    
    def num_players_with_orders(self):
        return (self.userround_set
                .filter(is_frozen=False)
                .exclude(last_trade=None)).count()
    
    def num_new_players(self):
        return (self.userround_set.filter(
                is_frozen=False,
                user__date_joined__gt=self.started_on,
                user__date_joined__lt=self.ends_on)).count()
    
    def num_new_players_with_orders(self):
        return (self.userround_set.filter(
                is_frozen=False,
                user__date_joined__gt=self.started_on,
                user__date_joined__lt=self.ends_on)
                .exclude(last_trade=None)).count()
    
    def avg_order_count(self):
        from pretweeting.apps.users.models import Order
        num_orders = Order.objects.filter(user_round__round=self).count()
        players_with_orders = self.num_players_with_orders()
        if players_with_orders == 0:
            return 0
        return num_orders / players_with_orders
    
    def orders_per_hour(self):
        from pretweeting.apps.users.models import Order
        num_orders = Order.objects.filter(user_round__round=self).count()
        duration = (self.ends_on - self.started_on)
        secs = duration.days * 86400 + duration.seconds
        hours = secs / 60.0 / 60.0
        if hours == 0:
            return 0
        return num_orders / hours