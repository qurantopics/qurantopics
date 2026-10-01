import pytest
from google.cloud.ndb import User
from controllers.page_controller import PageController
from controllers.exceptions import NoUserLoggedIn, UserNotPermittedToPerformOperation
from controllers.entities import AppAdmin


def test_require_login_when_anonymous(app):
    with app.test_request_context('/topics/add_edit'):
        controller = PageController()
        controller.user = None
        with pytest.raises(NoUserLoggedIn):
            controller.require_login()
        assert controller._redirect_url is not None
        assert "login" in controller._redirect_url


def test_require_login_when_logged_in(app):
    with app.test_request_context('/topics/add_edit'):
        controller = PageController()
        controller.user = User(email="user@example.com", _auth_domain="gmail.com")
        # Should not raise exception
        controller.require_login()


def test_require_user_owner(app):
    with app.test_request_context('/topics/view/1'):
        controller = PageController()
        owner = User(email="owner@example.com", _auth_domain="gmail.com")
        controller.user = owner
        # Same user should be permitted
        controller.require_user(owner)


def test_require_user_other_user_denied(app):
    with app.test_request_context('/topics/view/1'):
        controller = PageController()
        owner = User(email="owner@example.com", _auth_domain="gmail.com")
        other = User(email="other@example.com", _auth_domain="gmail.com")
        controller.user = other
        with pytest.raises(UserNotPermittedToPerformOperation):
            controller.require_user(owner)
        assert controller._redirect_url == "/"


def test_require_user_admin_allowed(app, seed_data):
    with app.test_request_context('/topics/view/1'):
        controller = PageController()
        owner = User(email="owner@example.com", _auth_domain="gmail.com")
        admin = User(email="admin@example.com", _auth_domain="gmail.com")
        controller.user = admin
        # Admin can access other user's resource
        controller.require_user(owner)


def test_is_logged_in_user_or_admin(app, seed_data):
    controller = PageController()
    owner = User(email="owner@example.com", _auth_domain="gmail.com")
    other = User(email="other@example.com", _auth_domain="gmail.com")
    admin = User(email="admin@example.com", _auth_domain="gmail.com")

    # Anonymous
    controller.user = None
    assert controller.is_logged_in_user_or_admin(owner) is False

    # Owner
    controller.user = owner
    assert controller.is_logged_in_user_or_admin(owner) is True

    # Other user
    controller.user = other
    assert controller.is_logged_in_user_or_admin(owner) is False

    # Admin
    controller.user = admin
    assert controller.is_logged_in_user_or_admin(owner) is True
