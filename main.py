import os
import logging

# Initialize local stubs for bundled services if running locally
# This MUST happen before other App Engine-related imports
if os.getenv('GAE_ENV') != 'standard':
    from google.appengine.api import apiproxy_stub_map, user_service_stub
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    apiproxy_stub_map.apiproxy.RegisterStub(
        'user', 
        user_service_stub.UserServiceStub(login_url='/login?continue=%s')
    )
    os.environ['APPLICATION_ID'] = 'dev~qurantopics'

from flask import Flask, send_from_directory, abort, request, redirect, make_response
from google.appengine.api import wrap_wsgi_app
from google.cloud import ndb as cloud_ndb

# Import our routes
from controllers.qurantopics import MainPage, SurasListPage, SurasDisplayPage, SearchTopics
from controllers.create_or_edit_topic import CreateOrEditTopic
from controllers.view_topic import ViewTopic
from controllers.admin import RemoveSura, ReputSura, EditAya

# Create Flask app
app = Flask(__name__, static_folder='static')

# Local Login Route for development
if os.getenv('GAE_ENV') != 'standard':
    @app.route('/login')
    def login_page():
        continue_url = request.args.get('continue', '/')
        email = request.args.get('email', 'admin@example.com')
        resp = make_response(redirect(continue_url))
        # Set a cookie that our middleware will use to 'log in' the user
        resp.set_cookie('dev_user', email)
        return resp

# Add routes to serve legacy static folders
@app.route('/stylesheets/<path:filename>')
def serve_stylesheets(filename):
    return send_from_directory('stylesheets', filename)

@app.route('/<path:filename>')
def serve_static_root(filename):
    # Match font files (from static/)
    if filename.endswith(('.ttf', '.otf', '.woff', '.woff2')):
        return send_from_directory('static', filename)
    # Match images (from static/images/)
    if filename.endswith(('.png', '.ico', '.jpg', '.jpeg', '.gif')):
        return send_from_directory('static/images', filename)
    # Match JS (from static/js/)
    if filename.endswith('.js'):
        return send_from_directory('static/js', filename)
    # Let other requests fall through to the route mapping
    abort(404)

# Initialize Cloud NDB Client
ndb_client = cloud_ndb.Client()

def ndb_wsgi_middleware(wsgi_app):
    def middleware(environ, start_response):
        # Local development user mocking
        if os.getenv('GAE_ENV') != 'standard':
            # Check for our dev_user cookie
            cookie_header = environ.get('HTTP_COOKIE', '')
            if 'dev_user=' in cookie_header:
                import re
                match = re.search(r'dev_user=([^;]+)', cookie_header)
                if match:
                    email = match.group(1)
                    # Set the environment variables that App Engine Users API expects
                    environ['USER_EMAIL'] = email
                    environ['USER_ID'] = '12345'
                    environ['USER_IS_ADMIN'] = '1' if 'admin' in email else '0'
                    environ['AUTH_DOMAIN'] = 'gmail.com'

        with ndb_client.context():
            return wsgi_app(environ, start_response)
    return middleware

# Wrap WSGI app for App Engine Bundled Services (Users API) and Cloud NDB
app.wsgi_app = ndb_wsgi_middleware(wrap_wsgi_app(app.wsgi_app))

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

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    app.run(host='127.0.0.1', port=8080, debug=True)
