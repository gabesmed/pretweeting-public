import datetime

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = 'pretweeting'

# for local access
DATABASE_USER = '---'
DATABASE_PASSWORD = '---'
DATABASE_HOST = ''

# for remote access
DATABASE_USER = '---'
DATABASE_PASSWORD = '---'
DATABASE_HOST = '---'

GAME_URL = 'local.pretweeting.com:8000'
DATA_URL = 'data.local.pretweeting.com:8000'

MEDIA_ROOT = '/Users/Gabe/pretweeting/media/'
MEDIA_URL = '/static_media/'
ADMIN_MEDIA_PREFIX = '/static_media/admin/'

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
SESSION_ENGINE = 'django.contrib.sessions.backends.file'

CACHE_LATEST_BATCH = False
CACHE_LATEST_BATCH_FOR = 60

TEMPLATE_DIRS = ("/Users/Gabe/pretweeting/templates")

BATCH_INTERVAL = 1 * 60 # ten minutes
BATCH_MAX_MESSAGES = 65535

LOCAL_DATA_DIR = "/Users/Gabe/pretweeting_data"
BULK_INSERT_DIR = "/Users/Gabe/pretweeting_data/bulk_insert"

# for the streaming API
TWITTER_USERNAME = '---'
TWITTER_PASSWORD = '---'
# for tweeting and DMing from pretweeting account
TWITTER_OAUTH_TOKEN = '---'
TWITTER_DM_SCREENNAME = '---'
# twitter authorization
CONSUMER_KEY = '---'
CONSUMER_SECRET = '---'

ROUND_LENGTH = datetime.timedelta(hours=1)
POST_TWEETS = True
TWEET_WIN = False