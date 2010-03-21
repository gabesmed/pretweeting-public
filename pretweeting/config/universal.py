DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Gabe Smedresman', 'gabesmed@yahoo.com')
)

MANAGERS = ADMINS

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'

SITE_ID = 1
USE_I18N = True

SECRET_KEY = '+a+dmo5*p^hl6(9+cfzq63%bw4yey^uhawr@hl7m8zsq%o+l_k'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

ROOT_URLCONF = 'pretweeting.views.game.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'djangodblog',
    'pretweeting.apps.users',
    'pretweeting.apps.batches',
    'pretweeting.apps.words',
    'pretweeting.apps.rounds',
)


TEMPLATE_CONTEXT_PROCESSORS = (
	'django.core.context_processors.auth',
	'django.core.context_processors.debug',
	'django.core.context_processors.i18n',
	'django.core.context_processors.media',
	'pretweeting.views.context_processors.notice',
)

AUTHENTICATION_BACKENDS = ('pretweeting.backends.MockBackend',)

AUTH_PROFILE_MODULE = 'users.userprofile'

LOGIN_REDIRECT_URL = '/'

CACHE_MIDDLEWARE_KEY_PREFIX = 'pretweeting'
CACHE_MIDDLEWARE_SECONDS = 300
SESSION_COOKIE_NAME = 'pretweeting'