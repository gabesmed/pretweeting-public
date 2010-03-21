import os
import sys

sys.path.append('/home/admin/pretweeting')

os.environ['DJANGO_SETTINGS_MODULE'] = 'pretweeting.settings_web_server'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
