#!/usr/bin/python
# coding: utf-8

########################

import sys
import xbmc
import xbmcgui

from resources.lib.helper import *
from resources.lib.tmdb_utils import *

########################

class TMDBVideos(object):

    def __init__(self,call_request):
        self.call = call_request['call']
        self.query = call_request['query']
        self.tmdb_id = call_request['tmdb_id']
        self.local_movies = call_request['local_movies']
        self.local_shows = call_request['local_shows']
        self.result = {}

        self.movie = get_bool(self.call,'movie')
        self.tvshow = get_bool(self.call,'tv')

        busydialog()

        if not self.tmdb_id:
            self.tmdb_id = self.search_video()

        if self.tmdb_id:
            self.cast, self.cast_dict, self.crew_dict = self.get_credits()
            self.result['details'] = self.get_details()
            self.result['cast'] = self.cast
            self.result['similar'] = self.get_similar()
            self.result['youtube'] = self.get_yt_videos()
            self.result['images'] = self.get_images()

        busydialog(close=True)


    def __getitem__(self, key):
        try:
            value = self.result[key]
            return value
        except KeyError:
            return


    def search_video(self):
        items = tmdb_search(self.call,self.query)

        try:
            result = items['results']

            if len(result) > 1:
                position = tmdb_select_dialog(result,self.call)
                if position < 0:
                    raise Exception
            else:
                position = 0

            tmdb_id = result[position]['id']

        except Exception:
            return ''

        return tmdb_id


    def get_details(self):
        details = tmdb_item_details(self.call,self.tmdb_id)
        details['crew'] = self.crew_dict

        li = list()
        if self.movie:
            list_item = tmdb_handle_movie(details,self.local_movies)
        elif self.tvshow:
            list_item = tmdb_handle_tvshow(details,self.local_shows)

        li.append(list_item)
        return li


    def get_credits(self):
        credits = tmdb_item_details(self.call,self.tmdb_id,'credits')
        cast = credits['cast']
        crew = credits['crew']
        li = list()

        for item in cast:
            list_item = tmdb_handle_cast(item)
            li.append(list_item)

        return li, cast, crew


    def get_similar(self):
        similar = tmdb_item_details(self.call,self.tmdb_id,'similar')
        similar = similar['results']

        li = list()

        if self.movie:
            for item in similar:
                if not item.get('release_date'):
                    item['release_date'] = '0'

            similar = sort_dict(similar,'release_date',True)
            for item in similar:
                list_item = tmdb_handle_movie(item,self.local_movies)
                li.append(list_item)

        elif self.tvshow:
            for item in similar:
                if not item.get('first_air_date'):
                    item['first_air_date'] = '0'

            similar = sort_dict(similar,'first_air_date',True)
            for item in similar:
                list_item = tmdb_handle_tvshow(item,self.local_shows)
                li.append(list_item)

        return li


    def get_images(self):
        images = tmdb_item_details(self.call,self.tmdb_id,'images',use_language=False)
        images = images['backdrops']
        li = list()

        for item in images:
            list_item = tmdb_handle_images(item)
            li.append(list_item)

        return li


    def get_yt_videos(self):
        videos = tmdb_item_details(self.call,self.tmdb_id,'videos')
        videos = videos['results']
        li = list()

        for item in videos:
            if item['site'] == 'YouTube':
                list_item = tmdb_handle_yt_videos(item)
                if not list_item == 404:
                    li.append(list_item)

        return li


