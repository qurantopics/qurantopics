import os
import logging

import json
from google.cloud import secretmanager

def load_secrets_from_vault():
    if os.getenv('GAE_ENV') == 'standard':
        try:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'qurantopics')
            name = f"projects/{project_id}/secrets/QURANTOPICS_SECRETS/versions/latest"
            
            response = client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")
            secrets = json.loads(payload)
            
            os.environ['GOOGLE_CLIENT_ID'] = secrets.get('GOOGLE_CLIENT_ID', '')
            os.environ['GOOGLE_CLIENT_SECRET'] = secrets.get('GOOGLE_CLIENT_SECRET', '')
            os.environ['SECRET_KEY'] = secrets.get('SECRET_KEY', 'default-prod-secret')
        except Exception as e:
            logging.error(f"Failed to load secrets from Secret Manager: {e}")

load_secrets_from_vault()

if os.getenv('GAE_ENV') != 'standard':
    os.environ['APPLICATION_ID'] = 'dev~qurantopics'


from flask import Flask, send_from_directory, abort, request, redirect, make_response
from google.cloud import ndb as cloud_ndb

# Import our routes
from controllers.qurantopics import MainPage, SurasListPage, SurasDisplayPage, SearchTopics
from controllers.create_or_edit_topic import CreateOrEditTopic
from controllers.view_topic import ViewTopic
from controllers.admin import RemoveSura, ReputSura, EditAya

# Create Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'default-dev-secret-key')

from controllers.auth_controller import auth_bp
app.register_blueprint(auth_bp)




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
        with ndb_client.context():
            return wsgi_app(environ, start_response)
    return middleware

# Wrap WSGI app for Cloud NDB
app.wsgi_app = ndb_wsgi_middleware(app.wsgi_app)

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
