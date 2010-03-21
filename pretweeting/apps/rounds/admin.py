from django.contrib import admin
from pretweeting.apps.rounds.models import Round

class RoundAdmin(admin.ModelAdmin):
    list_display = ('name', 'ends_on', 
            'num_players', 'num_players_with_orders',
            'avg_order_count',
            'num_new_players', 'num_new_players_with_orders',
            'orders_per_hour')

admin.site.register(Round, RoundAdmin)