import json
import uuid

import requests
import datetime

from django.http import HttpResponse, HttpResponseBadRequest
from django.core.mail import send_mail

from .db.users import insert_user, get_user_by_asap_token
from .db.games import insert_game, get_game
from . import utils

FB_APP_ID = "169924577279041"
FB_APP_SECRET = "5282a0aa51733f16f3ed227246bc8ec0"

# def index(request):
#     res = {'page': 'This is the index'}
#     return HttpResponse(json.dumps(res), content_type="application/json")
#
#
# def endpoint_example(request):
#     if 'team1' not in request.GET or 'team2' not in request.GET:
#         return HttpResponseBadRequest('Bad request')
#
#     res = {
#         'team1': request.GET['team1'],
#         'team2': request.GET.getlist('team2')
#     }
#     return HttpResponse(json.dumps(res), content_type="application/json")
#
#
# def params(request, number, slug):
#     res = {'number': number, 'slug': slug}
#     return HttpResponse(json.dumps(res), content_type="application/json")
#
#
# def params_regex(request, regex_var):
#     res = {'data_you_sent': regex_var}
#     return HttpResponse(json.dumps(res), content_type="application/json")


##### AUTHENTICATION #####

def login(request):
        """
        :param request: {'fb_access_token': str, 'device_id': str}. device_id is the ID of the device that we can send push notifications to
        :return: {'asap_access_token': str}
        
        TODO: Add an error message when user access token has expired and we need to
            take the user through login flow again.
        """

        # TODO: Check for ASAP Access Token header and return if valid???

        try:
            post_params = json.loads(request.read())
            fb_access_token = post_params['fb_access_token']
            # device_id = request.POST['device_id']
        except KeyError:
            return HttpResponseBadRequest("Missing required parameter")

        # Following docs here https://developers.facebook.com/docs/facebook-login/access-tokens/refreshing/
        params = {'client_id': FB_APP_ID,
                  'client_secret': FB_APP_SECRET,
                  'fb_exchange_token': fb_access_token,
                  'grant_type': 'fb_exchange_token'}
        try:
            from_fb = requests.get("https://graph.facebook.com/oauth/access_token", params=params).json()
            print(from_fb)
            fb_access_token = from_fb['access_token']
            expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=from_fb['expires_in'])
        except requests.exceptions.HTTPError as e:
            return HttpResponseBadRequest("Failed to reach Facebook")


        params = {'fields': 'id,name'}
        headers = {'Authorization': 'Bearer ' + fb_access_token}
        try:
            from_fb = requests.get("https://graph.facebook.com/me", params=params, headers=headers).json()
            name = from_fb['name'].split(' ')
            if len(name) == 1:
                first, last = name[0], None
            else:
                first, last = name[0], name[-1]
            profile_pic_url = "https://graph.facebook.com/%s/picture?redirect=0&width=100&height=100" % from_fb['id']
        except requests.exceptions.HTTPError as e:
            return HttpResponseBadRequest("Failed to reach Facebook")

        conn = utils.get_connection()
        asap_access_token = uuid.uuid4()
        insert_user(conn, first, last, fb_access_token,
                    profile_pic_url, asap_access_token)

        conn.commit()
        res = {'asap_access_token': str(asap_access_token)}
        return HttpResponse(json.dumps(res), content_type="application/json")


##### GAMES #####

def upcoming_games(request):
    """
    :param request: Only requires ASAP access token in the header key asap_access_token
    :return: {
           'auth_user': user,
           'games_in_progess': [game],
           'games_upcoming': [game],
           'past_games': [game]
           }
    """
    conn = utils.get_connection()
    user = get_user_by_asap_token(conn, utils.sanitize_uuid(request.META['Authorization']))
    if user is None:
        return HttpResponseBadRequest("Bad authorization")



    res = {'auth_user': user.to_dict(),
           'games_in_progress': [],
           'games_upcoming': [],
           'past_games': []}
    return HttpResponse(json.dumps(res), content_type="application/json")


def search(request):
    """
    :param request: {
          'radius_km': int,
          'start_time': dd-mmm-yyyy hh:mm,
          'end_time': dd-mmm-yyyy hh:mm,
          'sport': enum
        }
    :return: [game]
    """
    res = []
    return HttpResponse(json.dumps(res), content_type="application/json")


def join(request, game_id):
    """
    :param request: ASAP access token header
    :param game_id: int, in URL
    :return:
    """
    res = {'status': 'success'}
    return HttpResponse(json.dumps(res), content_type="application/json")


def host(request):
    """
    :param request: has data like:
        { 
           'game_title': str,
           'game_description': str,
           'max_players': int,
           'sport': sport_type_enum,
           'start_time': str('YYYY-MM-DD HH:MM'),
           'end_time': str('YYYY-MM-DD HH:MM'),
           'location_lng': float,
           'location_lat': float,
           'location_name': str
        }
    :return: {'game_id': game_id}
    """
    data = request.read()
    postdata = json.loads(data)
    try:
        game_title = postdata['game_title']
        game_description = postdata.get('game_description')
        max_players = utils.sanitize_int(postdata['max_players'])
        sport = utils.sanitize_sport(postdata['sport'])
        start_time = utils.sanitize_datetime(postdata['start_time'])
        end_time = utils.sanitize_datetime(postdata['end_time'])
        location_lng = utils.sanitize_float(postdata['location_lng'])
        location_lat = utils.sanitize_float(postdata['location_lat'])
        location_name = postdata['location_name']
        asap_access_token = request.META['Authorization']
    except KeyError as e:
        return HttpResponseBadRequest("Missing parameter " + str(e))

    l = locals()
    for x in ['max_players', 'sport', 'start_time', 'end_time', 'location_lng',
              'location_lat', 'location_name', 'asap_access_token']:
        if l[x] is None:
            return HttpResponseBadRequest("Missing or invalid parameter %s with bad value of %s" % (x, postdata[x]))

    conn = utils.get_connection()
    user = get_user_by_asap_token(conn, asap_access_token)
    if user is None:
        return HttpResponseBadRequest("Invalid access token.")

    game_id = insert_game(conn, user.id, game_title, game_description, max_players, sport, start_time,
                end_time, location_lat, location_lng, location_name)
    conn.commit()

    res = {'game_id': game_id}
    return HttpResponse(json.dumps(res), content_type="application/json")


def view(request, game_id):
    """
    :param request: ASAP access token header
    :param game_id: int, in URL
    :return: {'game_id': game_id,
               'host_id': user_id,
               'game_title': str,
               'game_description': str,
               'max_players': int,
               'sport': sport_type_enum,
               'start_time': str('YYYY-MM-DD HH:MM'),
               'end_time': str('YYYY-MM-DD HH:MM'),
               'location_lng': float,
               'location_lat': float,
               'location_name': str
               }
    """
    conn = utils.get_connection()
    game = get_game(conn, game_id)
    return HttpResponse(game.to_dict(), content_type="application/json")


##### NOTIFICATIONS #####

def subscribe2game(request, game_id):
    """
    :param request:
    :param game_id:
    :return:
    """
    res = {'status': 'success'}
    return HttpResponse(json.dumps(res), content_type="application/json")

