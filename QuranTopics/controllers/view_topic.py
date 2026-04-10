from google.appengine.ext import ndb
from controllers.view_objects import TopicEditView, TopicAyaView, TopicLine
from controllers.entities import Sura, Aya, Topic
from controllers.page_controller import PageController


class ViewTopic(PageController):

    def perform_get(self):
        leading_length = len('/topics/view/')
        topic_id = int(self.request.path[leading_length:])
        topic = Topic.get_by_id(topic_id)
        topic_lines = self.make_topic_lines(topic.get_ayat())
    
        self.template_values['topic'] = topic
        self.template_values['lines'] = topic_lines
        self.template_values['creating_user_or_admin'] = self.is_logged_in_user_or_admin(topic.created_by)
    
        return 'view_topic.html'
    
    
    def perform_post(self):
        if (self.request.get('delete')):
            topic_id = self.get_int('topic_id')
            topic = Topic.get_by_id(topic_id)
            self.require_user(topic.created_by)
            Topic.delete(topic)
            return "/"

    
    def make_topic_lines(self, ayat):
        import logging
        topic_lines = []
        prev_sura = -1
        prev_aya = -1
        for aya in ayat:
            topic_line = TopicLine()
            
            # Explicitly cast to int to prevent type mismatch (e.g. string vs int)
            current_sura = int(aya.sura.number)
            current_aya = int(aya.number)
            
            if current_sura != prev_sura or current_aya != prev_aya + 1:
                topic_line.new_section = True

            topic_line.sura_number = current_sura
            topic_line.sura_name = aya.sura.name if aya.sura else ""
            topic_line.aya_number = current_aya
            topic_line.aya_content = aya.content
            topic_lines.append(topic_line)
            
            prev_sura = current_sura
            prev_aya = current_aya
            
        return topic_lines
