import datetime
from django.conf import settings

# price for 100% of twitter talk
ALL_TWITTER_PRICE = 250

WORDS_PER_PAGE = 60

MIN_BUY_PRICE = 0.05

MIN_NUMBER_TO_BUY = 0
MIN_NUMBER_TO_SHOW = 3
    
COMMISSION = 0.05

# max slots for words you can have
MAX_SLOTS = 10000

# at most a word can take up 5 slots
TOP_WORD_SLOTS = 5

# quantity bought lookback
POPULARITY_LOOKBACK = datetime.timedelta(days=3)
