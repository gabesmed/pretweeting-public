import datetime, time
import math

from django.conf import settings
from pretweeting import consts

from pretweeting.apps.words.models import *
from pretweeting.apps.batches.models import *
from pretweeting.apps.rounds.models import *
from pretweeting.apps.users.models import *

from pretweeting.lib.timestamp import total_seconds