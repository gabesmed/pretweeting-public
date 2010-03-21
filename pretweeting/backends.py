from django.conf import settings

from pretweeting.apps.users.models import User, UserProfile

def get_or_create_user(username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist: 
        user = User.objects.create_user(username, '', 'haulL7solid!')
        user.save()

    try:
        user.get_profile()
    except UserProfile.DoesNotExist:  
        new_profile = UserProfile(user=user)
        new_profile.save()
    
    return user
  
class MockBackend:
    def authenticate(self, username, password=None):
        if password is not None and password != 'haulL7solid!':
            return None
        else:
            # otherwise, get or create the user
            return get_or_create_user(username)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None