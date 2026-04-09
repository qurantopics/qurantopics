import cgi
import logging
import os

from google.appengine.api import users
from controllers.entities import Sura, Topic, Aya
from controllers.page_controller import PageController


class MainPage(PageController):
    def perform_get(self):
        topics = Topic.query().fetch()
        self.template_values['topics'] = topics
        return 'index.html'


class SurasListPage(PageController):
    def perform_get(self):
        suras = Sura.query().order(Sura.number).fetch(114)
        self.template_values['suras'] = suras
        return 'suras_list.html'


class SurasDisplayPage(PageController):
    def perform_get(self):
        # We mapped this view to '/display_sura/<path:path>'
        # Flask gives it in kwargs as 'path', but PageController consumes self.request.path
        leading_length = len('/display_sura/')
        sura_number = int(self.request.path[leading_length:])
        sura = Sura.query(Sura.number == int(sura_number)).get()
        if sura:
            ayat = sura.aya_set.order(Aya.number).fetch(2000)
        else:
            ayat = []

        self.template_values['sura'] = sura
        self.template_values['ayat'] = ayat
        
        return 'sura_display.html'


class SearchTopics(PageController):
    def perform_get(self):
        return "/"

    def perform_post(self):
        search_for = self.request.get('search_for')
        topics = []
        if search_for:
            words = search_for.lower().split()
            query = Topic.query()
            for word in words:
                query = query.filter(Topic.search_words == word)
            topics = query.fetch()

        self.template_values['topics'] = topics
        
        return 'search_results.html'


class StaticPages(PageController):
    def perform_get(self):
        page_name = self.request.path[1:]
        return page_name + ".html"