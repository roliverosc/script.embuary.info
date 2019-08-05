#!/usr/bin/python
# coding: utf-8

########################

import sys
import xbmc
import xbmcgui

from resources.lib.helper import *
from resources.lib.tmdb_utils import *
from resources.lib.tmdb_person import *
from resources.lib.tmdb_video import *

########################

class TheMovieDB(object):
    def __init__(self,call,params):
        self.window_stack = []
        self.call = call
        self.tmdb_id = params.get('tmdb_id')
        self.query = remove_quotes(params.get('query'))

        self.call_params = {}
        self.call_params['local_shows'] = self.get_local_media('tvshow','VideoLibrary.GetTVShows',['title', 'originaltitle', 'year'])
        self.call_params['local_movies'] = self.get_local_media('movie','VideoLibrary.GetMovies',['title', 'originaltitle', 'year', 'imdbnumber'])

        self.entry_point()

    def get_local_media(self,dbtype,get,properties):
        items = json_call(get,properties,sort={'order': 'descending', 'method': 'year'})

        try:
            items = items['result']['%ss' % dbtype]
        except Exception:
            return

        local_items = []
        for item in items:
            local_items.append({'title': item.get('title',''), 'originaltitle': item.get('originaltitle',''), 'imdbnumber': item.get('imdbnumber',''), 'year': item.get('year',''), 'dbid': item.get('%sid' % dbtype,'')})

        return local_items

    def entry_point(self):
        self.call_params['tmdb_id'] = self.tmdb_id
        self.call_params['query'] = self.query
        self.call_params['call'] = self.call

        dialog = self.fetch_person() if self.call == 'person' else self.fetch_video()

        if dialog:
            self.dialog_manager(dialog)

    def fetch_person(self):
        data = TMDBPersons(self.call_params)
        if not data['person']:
            return

        return DialogPerson('script-embuary-person.xml', ADDON_PATH, 'default', '1080i', person=data['person'], movies=data['movies'], tvshows=data['tvshows'], images=data['images'])

    def fetch_video(self):
        data = TMDBVideos(self.call_params)
        if not data['details']:
            return

        return DialogVideo('script-embuary-video.xml', ADDON_PATH, 'default', '1080i', details=data['details'], cast=data['cast'], similar=data['similar'], youtube=data['youtube'], backdrops=data['images'])

    def dialog_manager(self,dialog):
        dialog.doModal()

        try:
            next_id = dialog['id']
            next_call = dialog['call']

            if next_call == 'back':
                self.dialog_history()

            if next_call == 'close':
                raise Exception

            if not next_id or not next_call:
                raise Exception

            self.window_stack.append(dialog)
            self.tmdb_id = next_id
            self.call = next_call
            self.entry_point()

        except Exception:
            self.quit()

    def dialog_history(self):
        if self.window_stack:
            dialog = self.window_stack.pop()
            self.dialog_manager(dialog)
        else:
            self.quit()

    def quit(self):
        self.window_stack = []


class DialogPerson(xbmcgui.WindowXMLDialog):
    def __init__(self,*args,**kwargs):
        self.first_load = True
        self.action = {}

        self.person = kwargs['person']
        self.movies = kwargs['movies']
        self.tvshows = kwargs['tvshows']
        self.images = kwargs['images']

    def __getitem__(self,key):
        return self.action[key]

    def __setitem__(self,key,value):
        self.action[key] = value

    def onInit(self):
        if self.first_load:
            self.add_items()

    def add_items(self):
        self.first_load = False

        self.cont0 = self.getControl(10051)
        self.cont0.addItems(self.person)
        self.cont1 = self.getControl(10052)
        self.cont1.addItems(self.movies)
        self.cont2 = self.getControl(10053)
        self.cont2.addItems(self.tvshows)
        self.cont3 = self.getControl(10054)
        self.cont3.addItems(self.images)

    def onAction(self, action):
        if action.getId() in [92,10]:
            self.action['id'] = ''
            self.action['call'] = 'back' if action.getId() == 92 else 'close'
            self.quit()

    def onClick(self,controlId):
        next_id = xbmc.getInfoLabel('Container(%s).ListItem.Property(id)' % controlId)
        next_call = xbmc.getInfoLabel('Container(%s).ListItem.Property(call)' % controlId)

        if next_call in ['person','movie','tv'] and next_id:
            self.action['id'] = next_id
            self.action['call'] = next_call
            self.quit()

        elif next_call == 'image':
            FullScreenImage(xbmc.getInfoLabel('Container(%s).ListItem.Art(thumb)' % controlId))

    def quit(self):
        self.close()


class DialogVideo(xbmcgui.WindowXMLDialog):
    def __init__(self,*args,**kwargs):
        self.first_load = True
        self.action = {}

        self.details = kwargs['details']
        self.cast = kwargs['cast']
        self.similar = kwargs['similar']
        self.youtube = kwargs['youtube']
        self.backdrops = kwargs['backdrops']

    def __getitem__(self,key):
        return self.action[key]

    def __setitem__(self,key,value):
        self.action[key] = value

    def onInit(self):
        if self.first_load:
            self.add_items()

    def add_items(self):
        self.first_load = False

        self.cont0 = self.getControl(10051)
        self.cont0.addItems(self.details)
        self.cont1 = self.getControl(10052)
        self.cont1.addItems(self.cast)
        self.cont2 = self.getControl(10053)
        self.cont2.addItems(self.similar)
        self.cont3 = self.getControl(10054)
        self.cont3.addItems(self.backdrops)
        self.cont4 = self.getControl(10055)
        self.cont4.addItems(self.youtube)

    def onAction(self, action):
        if action.getId() in [92,10]:
            self.action['id'] = ''
            self.action['call'] = 'back' if action.getId() == 92 else 'close'
            self.quit()

    def onClick(self,controlId):
        next_id = xbmc.getInfoLabel('Container(%s).ListItem.Property(id)' % controlId)
        next_call = xbmc.getInfoLabel('Container(%s).ListItem.Property(call)' % controlId)

        if next_call in ['person','movie','tv'] and next_id:
            self.action['id'] = next_id
            self.action['call'] = next_call
            self.quit()

        elif next_call == 'image':
            FullScreenImage(xbmc.getInfoLabel('Container(%s).ListItem.Art(thumb)' % controlId))

        elif next_call == 'youtube':
            self.action['call'] = 'close'
            execute('PlayMedia(plugin://plugin.video.youtube/play/?video_id=%s)' % xbmc.getInfoLabel('Container(%s).ListItem.Property(ytid)' % controlId))
            self.quit()

    def quit(self):
        self.close()


class FullScreenImage(object):
    def __init__(self,image):
        dialog = self.ShowImage('script-embuary-image.xml', ADDON_PATH, 'default', '1080i', image=image)
        dialog.doModal()
        del dialog

    class ShowImage(xbmcgui.WindowXMLDialog):
        def __init__(self,*args,**kwargs):
            self.path = kwargs['image']

        def onInit(self):
            self.image = self.getControl(1)
            self.image.setImage(self.path, False)