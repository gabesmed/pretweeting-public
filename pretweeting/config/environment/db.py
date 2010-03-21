import datetime

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = 'pretweeting'
DATABASE_USER = '---'
DATABASE_PASSWORD = '---'
DATABASE_HOST = ''
DATABASE_PORT = ''

MEDIA_ROOT = ''
MEDIA_URL = ''
ADMIN_MEDIA_PREFIX = ''
TEMPLATE_DIRS = ("")
CACHE_BACKEND = 'locmem:///'

BATCH_INTERVAL = 10 * 60 # ten minutes
BATCH_MAX_MESSAGES = 65535 # small integer limit

LOCAL_DATA_DIR = "/home/admin/pretweeting_data"
BULK_INSERT_DIR = "/home/admin/pretweeting_data/bulk_insert"

# for the streaming API
TWITTER_USERNAME = '---'
TWITTER_PASSWORD = '---'
# twitter auth
CONSUMER_KEY = '---'
CONSUMER_SECRET = '---'
# for DMing and tweeting from the pretweeting account
TWITTER_OAUTH_TOKEN = '---'
TWEET_WIN = True

ROUND_LENGTH = datetime.timedelta(days=3)
CACHE_LATEST_BATCH = False
CACHE_LATEST_BATCH_FOR = 60