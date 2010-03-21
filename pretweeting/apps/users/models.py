import datetime
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.conf import settings

from pretweeting import consts
from pretweeting.apps.batches.models import Batch
from pretweeting.apps.words.models import Word
from pretweeting.apps.rounds.models import Round
from pretweeting.apps.fields import BigIntegerField
from pretweeting.apps.words.templatetags import priceformat
from pretweeting.lib.timestamp import to_timestamp
from pretweeting.views.game.auth.utils import post_tweet, TwitterError, send_dm
from pretweeting.views.game.auth import oauth
from pretweeting.views.game.auth.views import CONSUMER, CONNECTION

VERY_SMALL = 0.01

class OrderError(Exception): pass

class UserProfile(models.Model):
    
    user = models.ForeignKey(User)
    access_token = models.CharField(max_length=255)
    tweets_ok = models.BooleanField(default=True)
    image_url = models.CharField(max_length=255)

    def __unicode__(self):
        return self.user.username

def get_active_user_round(self):
    try:
        return self.userround_set.filter(is_active=True).order_by('-id')[0]
    except IndexError:
        # none exist yet
        return self.new_user_round()

def new_user_round(self):
    
    # set all old ones to inactive
    self.userround_set.all().update(is_active=False)
    
    # and create a new one
    latest_round = Round.objects.latest()
    user_round = UserRound(user=self, round=latest_round, is_active=True)
    user_round.cash = user_round.current_value = latest_round.starting_cash
    user_round.save()
    return user_round

def frozen_at(self, round):
    try:
        return UserRound.objects.filter(user=self, round=round, is_frozen=True)[0]
    except IndexError:
        try:
            unfrozen = UserRound.objects.filter(user=self, round=round)[0]
            return unfrozen.copy_frozen()
        except IndexError:
            return None

User.frozen_at = frozen_at
User.get_active_user_round = get_active_user_round
User.new_user_round = new_user_round

class UserRound(models.Model):
    
    user = models.ForeignKey(User)
    round = models.ForeignKey(Round)
    created_on = models.DateTimeField(default=datetime.datetime.now)
    
    last_trade = models.DateTimeField(null=True, blank=True)
    cash = models.FloatField()
    current_value = models.FloatField()
    
    num_resets = models.PositiveSmallIntegerField('Resets', default=0)
    
    is_frozen = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def num_holdings(self):
        return self.holding_set.count()
    num_holdings.short_description = 'Holdings'
    
    def num_orders(self):
        return self.order_set.count()
    num_orders.short_description = 'Orders'
    
    def copy_frozen(self):
        "Make a frozen copy of this user round"
        if self.is_frozen:
            return self
        
        try:
            return UserRound.objects.filter(user=self.user, 
                round=self.round, is_frozen=True)[0]
        except IndexError:
            pass
        
        frozen = UserRound(user=self.user, round=self.round)
        frozen.last_trade = self.last_trade
        frozen.cash = self.cash
        frozen.current_value = self.current_value
        frozen.num_resets = self.num_resets
        frozen.is_frozen = True
        frozen.is_active = False
        frozen.save()
        
        for holding in self.holding_set.all():
            frozen_holding = Holding(user_round=frozen)
            frozen_holding.word = holding.word
            frozen_holding.quantity = holding.quantity
            frozen_holding.slots = holding.slots
            frozen_holding.current_value = holding.current_value
            frozen_holding.value_at_purchase = holding.value_at_purchase
            frozen_holding.save()
        
        return frozen
    
    def reset(self):
        "Reset this user round and up the count"
        self.holding_set.all().delete()
        self.order_set.all().delete()
        self.last_trade = None
        self.current_value = self.cash = self.round.starting_cash
        self.num_resets += 1
        self.save()
        
    def update_current_value(self):
        holding_value = (self.holding_set
                .aggregate(holding_value=Sum('current_value'))
        )['holding_value']
        holding_value = holding_value or 0
        
        self.current_value = self.cash + holding_value
        self.save()
    
    def change(self):
        return (100 
                * float(self.current_value - self.round.starting_cash) 
                / self.round.starting_cash)
    
    def sign(self):
        return cmp(self.current_value, self.round.starting_cash)
    
    def updown(self):
        if self.current_value > self.round.starting_cash:
            return 'up'
        elif self.current_value < self.round.starting_cash:
            return 'down'
        else:
            return 'nochange'
    
    def rank(self):
        above_me = (self.round.userround_set
                .exclude(id=self.id)
                .filter(current_value__gt=self.current_value))
        rank = above_me.count() + 1
        return rank
    
    def sell(self, word, quantity, tweeted=None):
        try:
            holding = self.holding_set.get(word=word)
        except Holding.DoesNotExist:
            raise OrderError("You don't own any of this word.")
        else:
            return holding.sell(quantity, tweeted=tweeted)
    
    def slots_held(self):
        if hasattr(self, '_slots_held'):
            return self._slots_held
        slots = 0
        for holding in self.holding_set.all():
            slots += holding.slots
        self._slots_held = slots
        return slots
    
    def slots_available(self):
        return consts.MAX_SLOTS - self.slots_held()
    
    def over_max_slots(self):
        return self.slots_held() > consts.MAX_SLOTS
    
    def slots_over_max(self):
        return self.slots_held() - consts.MAX_SLOTS
    
    def buy(self, word, quantity, tweeted=None):
        
        latest_batch = Batch.objects.latest()
        price = word.latest_price(force=True)
        buy_price = max(price, consts.MIN_BUY_PRICE)
        
        if buy_price == 0:
            raise OrderError("You can't buy a word with a price of $0.00.")
        
        buy_price_with_commission = buy_price
        
        slots_held = self.slots_held()
        slots_available = max(0, consts.MAX_SLOTS - slots_held)
        if quantity > slots_available:
            raise OrderError("You don't have enough slots available to buy %d of this word." % quantity)
        
        try:
            holding = self.holding_set.filter(word=word)[0]
        except IndexError:
            holding = None
        
        if self.cash < buy_price_with_commission * quantity:
            raise OrderError("You can't afford %s units" %
                    priceformat.quantity(quantity))
        
        if holding is not None:
            holding.record()
        else:
            holding = Holding(user_round=self, word=word)
            holding.quantity = 0
            holding.slots = 0
            
        holding.quantity += quantity
        holding.slots += quantity * word.slots
        holding.current_value = price * holding.quantity
        holding.value_at_purchase = buy_price_with_commission * holding.quantity
        holding.save()
        
        # this has to be after the holding because it relies on the
        # holding to be properly updated to calculate the new value
        self.cash -= buy_price_with_commission * quantity
        self.last_trade = datetime.datetime.now()
        self.save()
        self.update_current_value()
        
        new_order = Order(user_round=self, word=word, 
                order_type='B',
                quantity=quantity,
                price=buy_price_with_commission,
                tweeted=tweeted)
        new_order.save()
        
        return new_order
    
    def __unicode__(self):
        return '%s / %s ($%.02f)' % (self.round.name, self.user.username, self.current_value)

class Holding(models.Model):
    
    user_round = models.ForeignKey(UserRound)
    word = models.ForeignKey(Word)
     
    quantity = BigIntegerField() # total quantity
    slots = BigIntegerField() # total slots taken up
    
    created_on = models.DateTimeField(default=datetime.datetime.now)
    updated_on = models.DateTimeField(default=datetime.datetime.now)
    
    current_value = models.FloatField()
    value_at_purchase = models.FloatField()
    
    def save(self):
        self.updated_on = datetime.datetime.now()
        return super(Holding, self).save()
        
    def change(self):
        if self.value_at_purchase == 0:
            if self.current_value == 0:
                return 0
            else:
                return 100
        return (100 
                * float(self.current_value - self.value_at_purchase) 
                / self.value_at_purchase)
    
    def sign(self):
        return cmp(self.current_value, self.value_at_purchase)
            
    def sell(self, quantity, tweeted=None):
        
        price = self.word.latest_price(force=True)
        if abs(self.current_value - price * self.quantity) >= VERY_SMALL:
            raise OrderError("Some of our price data was inconsistent. Please try this order again.")
        
        penalized_price = price * (1 - consts.COMMISSION)
        
        if self.quantity < quantity:
            raise OrderError("You don't own that much of that word.")
        
        self.record()
        
        self.quantity -= quantity
        # never increase number of slots taken up, in case the slot value
        # has gone up. but don't decrease
        self.slots = min(self.slots, self.quantity * self.word.slots)
        
        self.current_value = price * self.quantity
        self.value_at_purchase = price * self.quantity
        self.save()
        
        # this has to be after the holding because it relies on the
        # holding to be properly updated to calculate the new value
        self.user_round.cash += penalized_price * quantity
        self.user_round.last_trade = datetime.datetime.now()
        self.user_round.save()
        self.user_round.update_current_value()
        
        new_order = Order(user_round=self.user_round, word=self.word, 
                price=penalized_price, quantity=quantity, 
                order_type='S', tweeted=tweeted)
        new_order.save()
        
        return new_order

    def record(self):
        "Record the holding up to this point in a history"
        try:
            last_history = self.holdinghistory_set.order_by('-history_end')[0]
            this_history_begin = last_history.history_end
        except IndexError:
            last_history = None
            this_history_begin = self.created_on
        
        new_history = HoldingHistory(holding=self)
        new_history.history_begin = this_history_begin
        new_history.history_end = datetime.datetime.now()
        new_history.value_begin = self.value_at_purchase
        new_history.value_end = self.current_value
        new_history.quantity = self.quantity
        new_history.save()
        
        return new_history

    def __unicode__(self):
        return self.word.content

          
class HoldingHistory(models.Model):
    holding = models.ForeignKey(Holding)
    
    history_begin = models.DateTimeField()
    history_end = models.DateTimeField()
    value_begin = models.FloatField()
    value_end = models.FloatField()
    
    quantity = BigIntegerField()
    
    unit_seconds = BigIntegerField()
    
    def change(self):
        if self.value_begin == 0:
            if self.value_end == 0:
                return 0
            else:
                return 100
        return (100 
                * float(self.value_end - self.value_begin) 
                / self.value_begin)
    
    def sign(self):
        return cmp(self.value_end, self.value_begin)
    
    @property
    def created_on(self):
        return self.history_end
    
    def save(self):
        t0 = to_timestamp(self.history_begin)
        t1 = to_timestamp(self.history_end)
        seconds = t1 - t0
        
        self.unit_seconds = self.quantity * seconds
        
        return super(HoldingHistory, self).save()

class Order(models.Model):
    
    created_on = models.DateTimeField(default=datetime.datetime.now)
    
    user_round = models.ForeignKey(UserRound)
    word = models.ForeignKey(Word)
    
    quantity = BigIntegerField()
    price = models.FloatField()
    
    order_type = models.CharField(max_length=1) # 'B' or 'S'
    
    tweeted = models.NullBooleanField(default=None)
    
    def user(self):
        return self.user_round.user
    
    @property
    def order_type_description(self):
        return "buy" if self.order_type == 'B' else "sell"
    
    @property
    def description(self):
        return "%s %s %s" % (
            self.order_type_description,
            priceformat.quantity(self.quantity),
            self.word.content
        )
    
    @property
    def confirmation(self):
        return "%s units %s for $%s." % (priceformat.quantity(self.quantity),
                "bought" if self.order_type == 'B' else "sold",
                priceformat.currency(self.cash_exchanged))
    
    @property
    def cash_exchanged(self):
        return self.price * self.quantity
    
    def tweet(self, access_token):
        if not access_token:
            raise ValueError("No access token")
        
        token = oauth.OAuthToken.from_string(access_token)

        sanitized_content = self.word.content.replace('#', '%23')
        sanitized_content = sanitized_content.replace('@', '%40')
        url = 'http://pretweeting.com/w/%s' % sanitized_content

        message = '@pretweeting %s -> see price at %s' % (self.description, url)
        try:
            response = post_tweet(CONSUMER, CONNECTION, token, message)
        except TwitterError, e:
            raise IOError("Couldn't post to twitter %s" % str(e))
    
    def __unicode__(self):
        return self.confirmation