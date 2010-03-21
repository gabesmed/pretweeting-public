from django.conf import settings
from django.db.models.fields import IntegerField

class BigIntegerField(IntegerField):
	empty_strings_allowed=False
	def get_internal_type(self):
		return "BigIntegerField"

	def db_type(self):
		return 'NUMBER(19)' if settings.DATABASE_ENGINE == 'oracle' else 'bigint'