import datetime
import requests

from django.conf import settings

FB_APP_ID = "169924577279041"


class FacebookAPIException(Exception):
    pass


def get_long_lived_access_token(short_fb_access_token):
    # Following docs here https://developers.facebook.com/docs/facebook-login/access-tokens/refreshing/
    params = {'client_id': FB_APP_ID,
              'client_secret': settings.FB_APP_SECRET,
              'fb_exchange_token': short_fb_access_token,
              'grant_type': 'fb_exchange_token'}

    try:
        from_fb = requests.get("https://graph.facebook.com/oauth/access_token", params=params).json()
    except requests.exceptions.HTTPError:
        raise FacebookAPIException("Failed to reach Facebook")
    if 'error' in from_fb:
        raise FacebookAPIException(from_fb['error'])

    fb_access_token = from_fb['access_token']
    expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=from_fb['expires_in'])
    return fb_access_token, expiry


def get_user_info(fb_access_token):
    params = {'fields': 'id,name,picture.type(large)'}
    headers = {'Authorization': 'Bearer ' + fb_access_token}
    try:
        from_fb = requests.get("https://graph.facebook.com/me", params=params, headers=headers).json()
        if 'error' in from_fb:
            raise FacebookAPIException(from_fb['error'])
        fb_id = from_fb['id']
        name = from_fb['name'].split(' ')
        if len(name) == 1:
            first, last = name[0], None
        else:
            first, last = name[0], name[-1]
        profile_pic_url = from_fb['picture']['data']['url']
    except requests.exceptions.HTTPError as e:
        raise FacebookAPIException("Failed to reach Facebook")

    return fb_id, first, last, profile_pic_url
