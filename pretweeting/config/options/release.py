DEBUG = False
TEMPLATE_DEBUG = DEBUG

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'djangodblog.DBLogMiddleware',
    # 'pretweeting.middleware.SQLLogMiddleware',
    'pretweeting.middleware.MultiHostMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware'
)