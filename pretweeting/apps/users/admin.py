from django.contrib import admin
from pretweeting.apps.users.models import (UserRound, Holding, Order, 
        UserProfile, HoldingHistory)
from django.contrib.auth.models import User, Group

class UserRoundAdmin(admin.ModelAdmin):
    
    class Media:
        css = {
            "all": ("custom_admin.css",)
        }
    
    list_filter = ('round', )
    list_display = ('user', 'round', 'current_value',
            'num_holdings', 'num_orders', 'num_resets',
            'is_active', 'is_frozen')
    search_fields = ('user__username',)
    ordering = ('round',)
    
    
    def change_view(self, request, object_id, extra_context=None):
        
        holdings = (Holding.objects.filter(user_round=object_id))
        word_histories = [holding.holdinghistory_set.order_by('history_begin')
                for holding in holdings]
        word_orders = [holding.user_round.order_set.filter(word=holding.word).order_by('created_on')
                for holding in holdings]
        word_gains = [sum([(history.value_end - history.value_begin) 
                for history in history_list]) 
                for history_list in word_histories]
        
        def combine(histories, orders):
        
            histories_and_orders = sorted(list(histories) + list(orders), 
                    key=lambda i: i.created_on)
        
            histories_and_orders = [
                    ((history_or_order, None)
                            if isinstance(history_or_order, HoldingHistory)
                            else (None, history_or_order))
                    for history_or_order in histories_and_orders]
            
            return histories_and_orders
        
        holding_histories = [(holding, combine(histories, orders), gains)
                for (holding, histories, orders, gains)
                in zip(holdings, word_histories, word_orders, word_gains)]
        
        userround = UserRound.objects.get(id=object_id)
        
        my_context = {
            'holding_histories': holding_histories,
            'sum_gains': sum(word_gains),
            'userround_delta': userround.current_value - userround.round.starting_cash
        }
        return super(UserRoundAdmin, self).change_view(request, object_id, 
                extra_context=my_context)
        

class OrderAdmin(admin.ModelAdmin):
    list_filter = ('created_on',)
    list_display = ('user', 'created_on', 'order_type', 'quantity', 'word', 'tweeted')
    ordering = ('-created_on',)
    search_fields = ('user_round__user__username',)
    raw_id_fields = ('word',)

admin.site.register(UserRound, UserRoundAdmin)
admin.site.register(Order, OrderAdmin)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    max_num = 1
    exclude = ('image_url', 'access_token')

class UserRoundInline(admin.TabularInline):
    model = UserRound
    exclude = ('round',)
    extra = 0

class MyUserAdmin(admin.ModelAdmin):
    inlines = [UserProfileInline, UserRoundInline]
    list_display = ('username', 'is_staff')
    list_filter = ('is_staff',)
    search_fields = ('username',)

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
admin.site.unregister(Group)