import os
import logging
import traceback
import sys
from flask import request, redirect, render_template, session, url_for
from flask.views import MethodView
from google.cloud.ndb import User
from controllers.exceptions import *
from controllers.entities import AppAdmin

class PageController(MethodView):
    
    def __init__(self):
        self.template_values = {}
        self.user = None
        self._redirect_url = None
    
    def get(self, *args, **kwargs):
        return self.perform_action(self.perform_get)
        
    def post(self, *args, **kwargs):
        return self.perform_action(self.perform_post)
    
    def redirect(self, url):
        self._redirect_url = url
    
    def perform_action(self, action):
        self.template_values = {}
        self._redirect_url = None
        self.set_user()
        
        view = None
        try:
            view = action()
        except UserAuthException as message:
            logging.debug("User authorization error: " + str(message))
            if self._redirect_url:
                return redirect(self._redirect_url)
        except Exception as exception:
            logging.error("Application error: " + str(type(exception)) + ": " + str(exception))
            traceback.print_exc()
            if self.user and AppAdmin.is_admin(self.user.email()):
                return "<br>".join(traceback.format_exc().splitlines())
            else:
                return redirect("/")

        if self._redirect_url:
            return redirect(self._redirect_url)

        if view is None:
            return "OK"

        try:
            if view.endswith(".html"):
                return self.display_view(view)
            else:
                return redirect(view)
        except Exception as exception:
            logging.error("Application error: " + str(type(exception)) + ": " + str(exception))
            traceback.print_exc()
            if self.user and AppAdmin.is_admin(self.user.email()):
                return "<br>".join(traceback.format_exc().splitlines())
            else:
                return redirect("/")
                
    def set_user(self):
        email = session.get('user_email')
        if email:
            self.user = User(email=email, _auth_domain='gmail.com')
            self.template_values['user'] = email.split('@')[0]
            user_link = url_for('auth.logout')
        else:
            self.user = None
            user_link = url_for('auth.login', **{'continue': request.url})

        self.template_values['user_link'] = user_link
            
    def display_view(self, view):
        return render_template(view, **self.template_values)
    
    def require_login(self):
        if not self.user:
            self.redirect(url_for('auth.login', **{'continue': request.url}))
            raise NoUserLoggedIn()
    
    def require_user(self, user):
        if not self.is_logged_in_user_or_admin(user):
            self.redirect('/')
            raise UserNotPermittedToPerformOperation(self.user.email() if self.user else 'Anonymous')
                         
    def is_logged_in_user_or_admin(self, user):
        is_admin = False
        if self.user:
            is_admin = AppAdmin.is_admin(self.user.email())
        return is_admin or self.user == user
    
    class WebRequestMock:
        def get(self, name):
            return request.values.get(name, '')
            
        def get_all(self, name):
            return request.values.getlist(name)
            
        @property
        def path(self):
            return request.path
            
        @property
        def uri(self):
            return request.url

    @property
    def request(self):
        return self.WebRequestMock()

    def get_int(self, name):
        value = self.request.get(name)
        if value and value.isdigit() and len(value) > 0:
            return int(value)
        return None
    
