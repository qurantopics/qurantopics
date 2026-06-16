import os
import logging
from flask import Blueprint, request, redirect, session, url_for, make_response
from authlib.integrations.flask_client import OAuth

auth_bp = Blueprint('auth', __name__)
oauth = OAuth()

# Configure Google OAuth
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID', 'mock-client-id'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', 'mock-client-secret'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@auth_bp.route('/login')
def login():
    if getattr(oauth, 'app', None) is None:
        from flask import current_app
        oauth.init_app(current_app._get_current_object())

    continue_url = request.args.get('continue', '/')
    session['continue_url'] = continue_url
    
    if os.getenv('GAE_ENV') != 'standard' and not os.environ.get('GOOGLE_CLIENT_ID'):
        # Local mock login
        email = request.args.get('email', 'admin@example.com')
        session['user_email'] = email
        return redirect(continue_url)
        
    redirect_uri = url_for('auth.auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/auth/callback')
def auth_callback():
    if getattr(oauth, 'app', None) is None:
        from flask import current_app
        oauth.init_app(current_app._get_current_object())

    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if user_info and user_info.get('email'):
            session['user_email'] = user_info['email']
            logging.info(f"User logged in: {session['user_email']}")
    except Exception as e:
        logging.error(f"OAuth callback error: {e}")
        
    continue_url = session.pop('continue_url', '/')
    return redirect(continue_url)

@auth_bp.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/')
