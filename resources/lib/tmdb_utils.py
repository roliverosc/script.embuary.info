#!/usr/bin/python
# coding: utf-8

########################

import json
import sys
import xbmc
import xbmcgui
import requests
import datetime

''' Python 2<->3 compatibility
'''
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from resources.lib.helper import *

########################

API_URL = 'https://api.themoviedb.org/3/'
IMAGEPATH = 'https://image.tmdb.org/t/p/original'
API_KEY = ADDON.getSettingString('tmdb_api_key')
DEFAULT_LANGUAGE = ADDON.getSettingString('language_code')
FALLBACK_LANGUAGE = 'en'

########################

def tmdb_call(request,error_check=False,error=ADDON.getLocalizedString(32019)):
    try:
        request = requests.get(request)
        if request.status_code != requests.codes.ok:

            if request.status_code == 401:
                error = ADDON.getLocalizedString(32022)
                raise Exception

            if request.status_code == 404:
                error = ADDON.getLocalizedString(32019)
                raise Exception

            else:
                error = 'Code ' + str(request.status_code)
                raise Exception

        result = request.json()

        if error_check:
            if len(result) == 0: raise Exception
            if 'results' in result and len(result['results']) == 0: raise Exception

        return result

    except Exception:
        tmdb_error(error)


def tmdb_query(action=None,call=None,get=None,use_language=True,language=DEFAULT_LANGUAGE,error_check=False,**kwargs):
    kwargs['api_key'] = API_KEY

    if use_language:
        kwargs['language'] = language

    if get is not None:
        call = call + '/' + get

    if call is not None:
        action = action + '/' + call

    url = API_URL + action
    url = '{0}?{1}'.format(url, urlencode(kwargs))

    return tmdb_call(url,error_check)


def tmdb_search(call,query,include_adult='false'):
    #/search/{call}?api_key=&language=&query={query}&page=1&include_adult=false
    result = tmdb_query(action='search',
                        call=call,
                        query=query,
                        include_adult=include_adult,
                        error_check=True
                        )
    return result


def tmdb_item_details(action,tmdb_id,get=None,use_language=True):
    #{action}/{id}?api_key=&language=
    #{action}/{id}/{get}?api_key=&language=
    result = tmdb_query(action=action,
                        call=str(tmdb_id),
                        get=get,
                        use_language=use_language
                        )

    if use_language and DEFAULT_LANGUAGE != FALLBACK_LANGUAGE and tmdb_fallback_details(result,action,get):
        result = tmdb_query(action=action,
                            call=str(tmdb_id),
                            get=get,
                            language=FALLBACK_LANGUAGE
                            )

    return result


def tmdb_fallback_details(result,action,get):
    if len(result) == 0: return True
    if 'results' in result and len(result['results']) == 0: return True
    if action == 'person' and get is None and not result['biography']: return True
    if action != 'person' and get is None and not result['overview']: return True

    return False


def tmdb_select_dialog(list,call):
    indexlist = []
    selectionlist = []

    if call == 'person':
        default_img = 'DefaultActor.png'
        img = 'profile_path'
        label = 'name'
        label2 = ''

    elif call == 'movie':
        default_img = 'DefaultVideo.png'
        img = 'poster_path'
        label = 'title'
        label2 = 'tmdb_get_year(item.get("release_date",""))'

    elif call == 'tv':
        default_img = 'DefaultVideo.png'
        img = 'poster_path'
        label = 'name'
        label2 = 'first_air_date'
        label2 = 'tmdb_get_year(item.get("first_air_date",""))'

    else:
        return

    index = 0
    for item in list:
        icon = IMAGEPATH + item[img] if item[img] is not None else ''
        list_item = xbmcgui.ListItem(item[label])
        list_item.setArt({'icon': default_img,'thumb': icon})

        try:
            list_item.setLabel2(str(eval(label2)))
        except Exception:
            pass

        selectionlist.append(list_item)
        indexlist.append(index)
        index += 1

    busydialog(close=True)

    selected = DIALOG.select(xbmc.getLocalizedString(424), selectionlist, useDetails=True)

    if selected == -1:
        return -1

    busydialog()

    return indexlist[selected]


def tmdb_calc_age(birthday,deathday=None):
    if deathday is not None:
        ref_day = deathday.split("-")
    elif birthday:
        date = datetime.date.today()
        ref_day = [date.year, date.month, date.day]
    else:
        return ''

    born = birthday.split('-')
    age = int(ref_day[0]) - int(born[0])

    if len(born) > 1:
        diff_months = int(ref_day[1]) - int(born[1])
        diff_days = int(ref_day[2]) - int(born[2])

        if diff_months < 0 or (diff_months == 0 and diff_days < 0):
            age -= 1

    return age


def tmdb_error(message=ADDON.getLocalizedString(32019)):
    busydialog(close=True)
    DIALOG.ok(ADDON.getLocalizedString(32000),message)


def tmdb_handle_person(item):
    icon = IMAGEPATH + item['profile_path'] if item['profile_path'] is not None else ''
    list_item = xbmcgui.ListItem(label=item['name'])
    list_item.setProperty('birthday', item.get('birthday',''))
    list_item.setProperty('deathday', item.get('deathday',''))
    list_item.setProperty('age', str(tmdb_calc_age(item.get('birthday',''),item.get('deathday',None))))
    list_item.setProperty('biography', item.get('biography',''))
    list_item.setProperty('place_of_birth', item.get('place_of_birth',''))
    list_item.setProperty('known_for_department', item.get('known_for_department',''))
    list_item.setProperty('gender', str(item.get('gender','')))
    list_item.setProperty('id', str(item.get('id','')))
    list_item.setProperty('call', 'person')
    list_item.setArt({'icon': 'DefaultActor.png','thumb': icon})

    return list_item


def tmdb_check_localdb(local_items,title,originaltitle,year,imdbnumber=False):
    year = tmdb_get_year(year)

    for item in local_items:
        dbid = item['dbid']
        if imdbnumber and item['imdbnumber'] == imdbnumber: return dbid
        try:
            if int(item['year']) == int(year):
                if item['originaltitle'] == originaltitle: return dbid
                if item['title'] == originaltitle: return dbid
                if item['title'] == title: return dbid
        except ValueError:
            pass

    return -1


def tmdb_handle_movie(item,local_items):
    icon = IMAGEPATH + item['poster_path'] if item['poster_path'] is not None else ''
    backdrop = IMAGEPATH + item['backdrop_path'] if item['backdrop_path'] is not None else ''

    label = item.get('title','')
    originaltitle = item.get('original_title','')
    imdbnumber = item.get('imdb_id','')
    premiered = item.get('release_date','')
    if premiered == '0': premiered = ''

    list_item = xbmcgui.ListItem(label=label)
    list_item.setInfo('video', {'title': label,
                                 'originaltitle': originaltitle,
                                 'dbid': tmdb_check_localdb(local_items,label,originaltitle,premiered,imdbnumber),
                                 'imdbnumber': imdbnumber,
                                 'rating': item.get('vote_average',''),
                                 'votes': item.get('vote_count',''),
                                 'premiered': premiered,
                                 'tagline': item.get('tagline',''),
                                 'plot': item.get('overview',''),
                                 'director': tmdb_join_items_by(item.get('crew',''),key_is='job',value_is='Director'),
                                 'country': tmdb_join_items(item.get('production_countries','')),
                                 'genre': tmdb_join_items(item.get('genres','')),
                                 'studio': tmdb_join_items(item.get('production_companies',''))}
                                 )
    list_item.setArt({'icon': 'DefaultVideo.png','thumb': icon,'fanart': backdrop})
    list_item.setProperty('id', str(item.get('id','')))
    list_item.setProperty('call', 'movie')
    list_item.setProperty('budget', str(tmdb_integer(item.get('budget',''))))
    list_item.setProperty('revenue', str(tmdb_integer(item.get('revenue',''))))

    return list_item


def tmdb_handle_tvshow(item,local_items):
    icon = IMAGEPATH + item['poster_path'] if item['poster_path'] is not None else ''
    backdrop = IMAGEPATH + item['backdrop_path'] if item['backdrop_path'] is not None else ''

    label = item.get('name','')
    originaltitle = item.get('original_name','')
    premiered = item.get('first_air_date','')
    if premiered == '0': premiered = ''

    list_item = xbmcgui.ListItem(label=label)
    list_item.setInfo('video', {'title': label,
                                 'originaltitle': originaltitle,
                                 'dbid': tmdb_check_localdb(local_items,label,originaltitle,premiered),
                                 'status': item.get('status',''),
                                 'rating': item.get('vote_average',''),
                                 'votes': item.get('vote_count',''),
                                 'premiered': premiered,
                                 'season': str(item.get('number_of_seasons','')),
                                 'episode': str(item.get('number_of_episodes','')),
                                 'plot': item.get('overview',''),
                                 'director': tmdb_join_items(item.get('created_by','')),
                                 'genre': tmdb_join_items(item.get('genres','')),
                                 'studio': tmdb_join_items(item.get('networks',''))}
                                 )
    list_item.setArt({'icon': 'DefaultVideo.png','thumb': icon,'fanart': backdrop})
    list_item.setProperty('id', str(item.get('id','')))
    list_item.setProperty('call', 'tv')

    return list_item


def tmdb_handle_images(item):
    icon = IMAGEPATH + item['file_path'] if item['file_path'] is not None else ''
    list_item = xbmcgui.ListItem(label=str(item['width']) + 'x' + str(item['height']) + 'px')
    list_item.setArt({'icon': 'DefaultPicture.png','thumb': icon})
    list_item.setProperty('call', 'image')

    return list_item


def tmdb_handle_cast(item):
    icon = IMAGEPATH + item['profile_path'] if item['profile_path'] is not None else ''
    list_item = xbmcgui.ListItem(label=item['name'])
    list_item.setLabel2(item['character'])
    list_item.setArt({'icon': 'DefaultActor.png','thumb': icon})
    list_item.setProperty('id', str(item.get('id','')))
    list_item.setProperty('call', 'person')

    return list_item


def tmdb_handle_yt_videos(item):
    icon = 'https://img.youtube.com/vi/%s/0.jpg' % str(item['key'])

    request = requests.get(icon)
    if request.status_code != requests.codes.ok:
        return 404

    list_item = xbmcgui.ListItem(label=item['name'])
    list_item.setArt({'icon': 'DefaultVideo.png','thumb': icon})
    list_item.setProperty('ytid', str(item['key']))
    list_item.setProperty('call', 'youtube')

    return list_item


def tmdb_join_items_by(item,key_is,value_is,key='name'):
    values = []
    for value in item:
        if value[key_is] == value_is:
            values.append(value[key])

    return get_joined_items(values)


def tmdb_join_items(item,key='name'):
    values = []
    for value in item:
        values.append(value[key])

    return get_joined_items(values)


def tmdb_integer(item):
    if item > 0:
        return item
    return ''


def tmdb_get_year(item):
    try:
        year = str(item)[:-6]
        return year
    except Exception:
        return ''