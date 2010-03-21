import datetime

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = 'pretweeting'
DATABASE_USER = '---'
DATABASE_PASSWORD = '---'
DATABASE_HOST = '---'

MEDIA_ROOT = '/home/admin/pretweeting/media/'
MEDIA_URL = '/static_media/'
ADMIN_MEDIA_PREFIX = '/static_media/admin/'

GAME_URL = 'pretweeting.com'
DATA_URL = 'data.pretweeting.com'

TEMPLATE_DIRS = (
    "/home/admin/pretweeting/templates"
)

LOCAL_DATA_DIR = "/home/admin/pretweeting_data"

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

CACHE_LATEST_BATCH = True
CACHE_LATEST_BATCH_FOR = 60

# twitter auth
CONSUMER_KEY = '---'
CONSUMER_SECRET = '---'

POST_TWEETS = True
TWITTER_DM_SCREENNAME = 'pretweeting'