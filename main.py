import logging
from flask import Flask
from google.appengine.api import wrap_wsgi_app
from google.appengine.ext import ndb

# Import our routes
from controllers.qurantopics import MainPage, SurasListPage, SurasDisplayPage, SearchTopics, StaticPages
from controllers.create_or_edit_topic import CreateOrEditTopic
from controllers.view_topic import ViewTopic
from controllers.admin import RemoveSura, ReputSura, EditAya

# Create Flask app
app = Flask(__name__, static_folder='static')

# Wrap WSGI app for App Engine Bundled Services (Users API & NDB)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

# Main mapping routes
app.add_url_rule('/', view_func=MainPage.as_view('main_page'))
app.add_url_rule('/list_suras', view_func=SurasListPage.as_view('suras_list'))
app.add_url_rule('/display_sura/<path:path>', view_func=SurasDisplayPage.as_view('suras_display'))
app.add_url_rule('/search', view_func=SearchTopics.as_view('search'))

# Topics
app.add_url_rule('/topics/add_edit', view_func=CreateOrEditTopic.as_view('create_edit_topic'))
app.add_url_rule('/topics/view/<int:topic_id>', view_func=ViewTopic.as_view('view_topic'))

# Admin
app.add_url_rule('/admin/remove_sura', view_func=RemoveSura.as_view('admin_remove_sura'))
app.add_url_rule('/admin/reput_sura', view_func=ReputSura.as_view('admin_reput_sura'))
app.add_url_rule('/admin/edit_aya', view_func=EditAya.as_view('admin_edit_aya'))

# Static pages catch-all
app.add_url_rule('/<path:path>', view_func=StaticPages.as_view('static_pages'))

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    app.run(host='127.0.0.1', port=8080, debug=True)
