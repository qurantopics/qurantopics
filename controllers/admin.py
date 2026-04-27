# coding: utf8

import logging

from flask.views import MethodView
from flask import request
from google.cloud import ndb

from controllers.entities import Sura, Aya, Topic
from controllers.page_controller import PageController


class RemoveSura(MethodView):

    def get(self):
        sura_number = int(request.values.get('sura'))
        sura = Sura.query(Sura.number == sura_number).get()
        if sura:
            ndb.delete_multi(sura.aya_set.fetch(keys_only=True))
        return "OK"


class ReputSura(MethodView):

    def get(self):
        sura_number = int(request.values.get('sura'))
        sura = Sura.query(Sura.number == sura_number).get()
        if sura:
            ayat = Aya.query(Aya.sura_key == sura.key).fetch(1000)
            ndb.put_multi(ayat)
            return "reput num of ayat: " + str(len(ayat))
        return "Not found"
        

class EditAya(PageController):

    def perform_get(self):
        sura_number = int(self.request.get('sura'))
        aya_number = int(self.request.get('aya'))
        
        return self.display_page(sura_number, aya_number)
        
        
    def display_page(self, sura_number, aya_number):
        
        sura = Sura.get_by_number(sura_number)
        ayat = sura.aya_set.filter(Aya.number == aya_number).fetch(1000)

        aya_topics = []
        for aya in ayat:
            key_str = aya.key.urlsafe().decode('utf-8')
            aya_topics.append("مفتاح = " + key_str)
            topics = self.get_topics_for_aya(aya)
            for topic in topics:
                aya_topics.append("موضوع = " + str(topic.topic_id))
        
        
        self.template_values['aya'] = ayat[0] if ayat else None
        self.template_values['aya_topics'] = aya_topics
        self.template_values['ayat'] = ayat
        self.template_values['show_delete'] = len(ayat) > 1
 
        return 'edit_aya.html'
    
        
    def perform_post(self):
        if (self.request.get('edit')):
            aya_key = self.request.get('aya_key')
            aya = ndb.Key(urlsafe=aya_key).get()
            if aya:
                aya.content = self.request.get('aya_content')
                aya.put()
                return self.display_page(aya.sura.number, aya.number)
            return "Aya not found"
        
        elif (self.request.get('delete')):
            aya_key = self.request.get('aya_key')
            aya = ndb.Key(urlsafe=aya_key).get()
            if aya:
                topics = self.get_topics_for_aya(aya)
                if len(topics) == 0:
                    aya.key.delete()
                return self.display_page(aya.sura.number, aya.number)
            return "Aya not found"
        
        
    def get_topics_for_aya(self, aya):
        return Topic.query(Topic.ayat_keys == aya.key).fetch(1000)