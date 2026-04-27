# coding: utf8

import logging
from google.cloud import ndb
from controllers.view_objects import TopicEditView, TopicAyaView, TopicLine
from controllers.entities import Sura, Aya, Topic
from controllers.page_controller import PageController


class CreateOrEditTopic(PageController):
    
    topic_edit_view = None

    def perform_get(self):
        self.require_login()
        self.topic_edit_view = TopicEditView()
        self.template_values['topic'] = self.topic_edit_view
        return 'edit_topic.html'
    

    def perform_post(self):
        self.require_login()
        self.populate_view()

        if (self.request.get('add')):
            self.validate_requirements_for_add()
            if not self.topic_edit_view.error:
                sura = Sura.get_by_number(self.topic_edit_view.sura)
                ayat = sura.get_ayat_query_in_range(self.topic_edit_view.from_aya, self.topic_edit_view.to_aya)
                added_ayat = self.make_ayat_display_from_ayat(ayat)
                self.merge_added_ayat_to_topic_ayat(added_ayat)
        elif (self.request.get('edit')):
            self.edit_topic()
        elif (self.request.get('remove')):
            self.remove_selected()
        elif (self.request.get('move_to_position')):
            self.move_selected_to_position()
        elif (self.request.get('save')):
            self.save_topic()
        else:
            logging.info("operation not handled")

        self.template_values['topic'] = self.topic_edit_view
    
        return 'edit_topic.html'
    
    
    def validate_requirements_for_add(self):
        if not self.topic_edit_view.sura or not self.topic_edit_view.from_aya:
            self.topic_edit_view.error = "لم يتم ادخال رقم السورة أو الآية بصورة صحيحة"
    
    
    def save_topic(self):
        title = self.request.get('title')
        if not title:
            self.topic_edit_view.error = "لم يتم إدخال عنوان الموضوع"
        elif not self.topic_edit_view.ayat_display:
            self.topic_edit_view.error = "الموضوع لا يتضمن أي آيات"
        else:
            if self.topic_edit_view.topic_id:
                topic = Topic.get_by_id(self.topic_edit_view.topic_id)
                self.require_user(topic.created_by)
            else:
                topic = Topic()
                topic.created_by = self.user
                topic.put()
                topic.topic_id = topic.key.id()
                self.topic_edit_view.topic_id = topic.topic_id 
            topic.title = title
            ayat_keys = self.make_ayat_keys_from_ayat_display(self.topic_edit_view.ayat_display)
            topic.ayat_keys = ayat_keys
            topic.put()
            self.topic_edit_view.message = "تم حفظ الموضوع"

    
    def edit_topic(self):
        topic = Topic.get_by_id(self.topic_edit_view.topic_id)
        self.require_user(topic.created_by)
        self.topic_edit_view.title = topic.title
        self.topic_edit_view.ayat_display = self.make_ayat_display_from_ayat(topic.get_ayat())
        

    def populate_view(self):
        self.topic_edit_view = TopicEditView()
        self.topic_edit_view.topic_id = self.get_int('topic_id')
        self.topic_edit_view.title = self.request.get('title')
        self.topic_edit_view.sura = self.get_int('sura')
        self.topic_edit_view.from_aya = self.get_int('from_aya')
        to_aya = self.get_int('to_aya')
        if not to_aya:
            to_aya = self.topic_edit_view.from_aya
        self.topic_edit_view.to_aya = to_aya
        self.topic_edit_view.position = self.get_int('position')
        self.topic_edit_view.to_position = self.get_int('to_position')
        self.populate_ayat()


    def populate_ayat(self):
        count = 1
        ayat_display = []
        while (self.request.get("sura_" + str(count))):
            aya_display = TopicAyaView()
            aya_display.position = self.get_position(count)
            aya_display.selected = self.get_selected(count)
            aya_display.sura_number = self.get_sura(count)
            aya_display.sura_name = self.get_sura_name(count)
            aya_display.aya_number = self.get_aya(count)
            aya_display.aya_content = self.get_aya_content(count)
            aya_display.aya_key = self.get_aya_key(count)
            ayat_display.append(aya_display)
            count = count + 1
        
        ayat_display.sort(key = lambda aya: aya.position)
        self.topic_edit_view.ayat_display = ayat_display
        
    
    def make_ayat_display_from_ayat(self, ayat):
        ayat_display = []
        for aya in ayat:
            aya_display = TopicAyaView()
            aya_display.sura_number = aya.sura.number
            aya_display.sura_name = aya.sura.name
            aya_display.aya_number = aya.number
            aya_display.aya_content = aya.content
            aya_display.aya_key = aya.key.urlsafe().decode('utf-8')
            ayat_display.append(aya_display)
        return ayat_display

            
    def make_ayat_keys_from_ayat_display(self, ayat_display):
        ayat_keys = []
        for aya_display in ayat_display:
            aya_key = ndb.Key(urlsafe=aya_display.aya_key)
            ayat_keys.append(aya_key)
        return ayat_keys
            
    
    def merge_added_ayat_to_topic_ayat(self, added_ayat):
        topic_ayat = self.topic_edit_view.ayat_display
        position = self.topic_edit_view.position
        
        ayat_to_add = []
        for aya_display in added_ayat:
            if not self.list_contains_aya(topic_ayat, aya_display):
                ayat_to_add.append(aya_display)
        
        if position is not None and position >= 1 and position <= len(topic_ayat):
            position = position - 1
            topic_ayat = topic_ayat[:position] + ayat_to_add + topic_ayat[position:]
        else:
            topic_ayat.extend(ayat_to_add)
            
        self.topic_edit_view.ayat_display = topic_ayat
    
    
    def list_contains_aya(self, ayat_display, aya_display):
        for list_aya in ayat_display:
            if self.same_aya(list_aya, aya_display):
                return True
        return False
    
    def remove_selected(self):
        new_set = []
        for aya_display in self.topic_edit_view.ayat_display:
            if (not aya_display.selected):
                new_set.append(aya_display)
        
        self.topic_edit_view.ayat_display = new_set
    
    
    def move_selected_to_position(self):
        to_position = self.topic_edit_view.to_position
        before_position = []
        selected = []
        after_position = []
        count = 1
        for aya_display in self.topic_edit_view.ayat_display:
            if aya_display.selected:
                selected.append(aya_display)
            elif count < to_position:
                before_position.append(aya_display)
            else:
                after_position.append(aya_display)
            count += 1
        
        self.topic_edit_view.ayat_display = before_position + selected + after_position
    
    
    def same_aya(self, aya1, aya2):
        return aya1.sura_number == aya2.sura_number and aya1.aya_number == aya2.aya_number
        
    
    def get_position(self, order):
        return self.get_int("position_" + str(order))

    
    def get_sura(self, order):
        return self.get_int("sura_" + str(order))
    

    def get_sura_name(self, order):
        return self.request.get("sura_name_" + str(order))
    

    def get_aya(self, order):
        return self.get_int("aya_" + str(order))
    
    
    def get_aya_content(self, order):
        return self.request.get("aya_content_" + str(order))
    
    
    def get_aya_key(self, order):
        return self.request.get("aya_key_" + str(order))
    
    
    def get_selected(self, order):
        return self.request.get("selected_" + str(order)) == "on"
