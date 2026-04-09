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
        topic_lines = []
        prev_sura = -1
        prev_aya = -1
        for aya in ayat:
            topic_line = TopicLine()
            if aya.sura.number != prev_sura or aya.number != prev_aya + 1:
                topic_line.new_section = True

            topic_line.sura_number = aya.sura.number
            topic_line.sura_name = aya.sura.name
            topic_line.aya_number = aya.number
            topic_line.aya_content = aya.content
            topic_lines.append(topic_line)
            prev_sura = aya.sura.number
            prev_aya = aya.number
        return topic_lines
