import os
import logging
import traceback
import sys
from flask import request, redirect, render_template
from flask.views import MethodView
from google.appengine.api import users
from controllers.exceptions import *

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
            if users.is_current_user_admin():
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
            if users.is_current_user_admin():
                return "<br>".join(traceback.format_exc().splitlines())
            else:
                return redirect("/")
                
    def set_user(self):
        user = users.get_current_user()
        if user:
            self.user = user
            self.template_values['user'] = user.nickname()
            user_link = users.create_logout_url('/')
        else:
            user_link = users.create_login_url(request.url)

        self.template_values['user_link'] = user_link
            
    def display_view(self, view):
        return render_template(view, **self.template_values)
    
    def require_login(self):
        if not self.user:
            self.redirect(users.create_login_url(request.url))
            raise NoUserLoggedIn()
    
    def require_user(self, user):
        if not self.is_logged_in_user_or_admin(user):
            self.redirect('/')
            raise UserNotPermittedToPerformOperation(self.user.email() if self.user else 'Anonymous')
                         
    def is_logged_in_user_or_admin(self, user):
        return users.is_current_user_admin() or self.user == user
    
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
    
