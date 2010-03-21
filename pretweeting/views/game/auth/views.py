import oauth, httplib, time, datetime
from django.utils import simplejson

from django.http import *
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.contrib.auth import login, authenticate

from pretweeting.apps.users.models import User
from pretweeting.views.game.auth.utils import *

CONSUMER = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
CONNECTION = httplib.HTTPSConnection(SERVER)

def unauth(request):
    request.session.clear()
    request.session['notice'] = 'Logged out!'
    return HttpResponseRedirect('/')

def auth(request):
    "/auth/"
    try:
        token = get_unauthorised_request_token(CONSUMER, CONNECTION)
        auth_url = get_authorisation_url(CONSUMER, token)
    except httplib.CannotSendRequest:
        request.session['notice'] = "Sorry, there was an error on our side logging you in. Please try again, and let @pretweeting know if it consistently fails."
        return HttpResponseRedirect('/')  
    except KeyError:
        request.session['notice'] = "Sorry, there was an intermittent error logging you in. Please try again."
        return HttpResponseRedirect('/')
    
    request.session['unauthed_token'] = token.to_string()   
    return HttpResponseRedirect(auth_url)

def return_(request):
    "/return/"
    unauthed_token = request.session.get('unauthed_token', None)
    if not unauthed_token:
        request.session['notice'] = "Sorry, we couldn't properly process your authentication. Please try again, and let @pretweeting know if it consistently fails."
        return HttpResponseRedirect('/')
    token = oauth.OAuthToken.from_string(unauthed_token)
    
    if token.key != request.GET.get('oauth_token', 'no-token'):
        request.session['notice'] = "Sorry, we couldn't log you in."
        return HttpResponseRedirect('/')
    
    try:
        access_token = exchange_request_token_for_access_token(
                CONSUMER, CONNECTION, token)
    except KeyError:
        request.session['notice'] = "Sorry, we experienced an error logging you in. Please try again, and let @pretweeting know if it consistently fails."
        return HttpResponseRedirect('/')
    
    request.session['access_token'] = access_token.to_string()
        
    # Check if the token works on Twitter
    auth = is_authenticated(CONSUMER, CONNECTION, access_token)
    if auth:
        # Load the credidentials from Twitter into JSON
        creds = simplejson.loads(auth)
        screen_name = creds['screen_name'] # Get the name
        # and profile image
        profile_image_url = creds.get('profile_image_url', '')
        
        user = authenticate(username=screen_name)
        # save the access token
        profile = user.get_profile()
        profile.access_token = access_token.to_string()
        profile.image_url = profile_image_url
        profile.save()
        
        try:
            follow(CONSUMER, CONNECTION, access_token, 
                    settings.TWITTER_DM_SCREENNAME)
        except TwitterError:
            pass
        
        login(request, user)
        request.session['notice'] = "Welcome to pretweeting!"
        return HttpResponseRedirect('/')
    else:
        request.session['notice'] = "Sorry, you weren't authenticated by Twitter."
        return HttpResponseRedirect('/')
