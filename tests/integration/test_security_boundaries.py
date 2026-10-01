import pytest
from google.cloud.ndb import User
from controllers.entities import Topic, Sura, Aya


@pytest.fixture
def user_a_topic(seed_data):
    sura1 = seed_data["sura1"]
    aya1 = sura1.get_aya_by_number(1)
    topic = Topic(
        topic_id=501,
        title="موضوع المستخدم أ",
        ayat_keys=[aya1.key],
        created_by=User(email="user_a@example.com", _auth_domain="gmail.com")
    )
    topic.put()
    return topic


def test_user_cannot_edit_other_user_topic(app, user_a_topic):
    # Logged in as User B
    client_b = app.test_client()
    with client_b.session_transaction() as sess:
        sess['user_email'] = 'user_b@example.com'

    resp = client_b.post('/topics/add_edit', data={
        'edit': 'عدل الموضوع',
        'topic_id': str(user_a_topic.topic_id)
    }, follow_redirects=False)

    # Should redirect away (to /)
    assert resp.status_code in (301, 302)
    assert resp.headers.get('Location') == '/'


def test_user_cannot_save_over_other_user_topic(app, user_a_topic):
    # Logged in as User B attempting to overwrite User A's topic
    client_b = app.test_client()
    with client_b.session_transaction() as sess:
        sess['user_email'] = 'user_b@example.com'

    resp = client_b.post('/topics/add_edit', data={
        'save': 'احفظ الموضوع',
        'topic_id': str(user_a_topic.topic_id),
        'title': 'عنوان مخترق',
        'sura_1': '1',
        'aya_1': '1',
        'aya_key_1': user_a_topic.ayat_keys[0].urlsafe().decode('utf-8')
    }, follow_redirects=False)

    assert resp.status_code in (301, 302)
    assert resp.headers.get('Location') == '/'

    # Verify original title was not changed
    fresh_topic = Topic.get_by_id(user_a_topic.topic_id)
    assert fresh_topic.title == "موضوع المستخدم أ"


def test_user_cannot_delete_other_user_topic(app, user_a_topic):
    client_b = app.test_client()
    with client_b.session_transaction() as sess:
        sess['user_email'] = 'user_b@example.com'

    resp = client_b.post(f'/topics/view/{user_a_topic.topic_id}', data={
        'delete': 'احذف الموضوع',
        'topic_id': str(user_a_topic.topic_id)
    }, follow_redirects=False)

    assert resp.status_code in (301, 302)
    assert resp.headers.get('Location') == '/'

    # Verify topic is still intact
    assert Topic.get_by_id(user_a_topic.topic_id) is not None


def test_anonymous_cannot_delete_topic(client, user_a_topic):
    resp = client.post(f'/topics/view/{user_a_topic.topic_id}', data={
        'delete': 'احذف الموضوع',
        'topic_id': str(user_a_topic.topic_id)
    }, follow_redirects=False)

    assert resp.status_code in (301, 302)
    assert Topic.get_by_id(user_a_topic.topic_id) is not None


def test_admin_can_edit_any_topic(app, user_a_topic, seed_data):
    admin_client = app.test_client()
    with admin_client.session_transaction() as sess:
        sess['user_email'] = 'admin@example.com'

    resp = admin_client.post('/topics/add_edit', data={
        'save': 'احفظ الموضوع',
        'topic_id': str(user_a_topic.topic_id),
        'title': 'عنوان معدل بواسطة المدير',
        'sura_1': '1',
        'aya_1': '1',
        'aya_key_1': user_a_topic.ayat_keys[0].urlsafe().decode('utf-8')
    })

    assert resp.status_code == 200
    fresh_topic = Topic.get_by_id(user_a_topic.topic_id)
    assert fresh_topic.title == 'عنوان معدل بواسطة المدير'


def test_admin_can_delete_any_topic(app, user_a_topic, seed_data):
    admin_client = app.test_client()
    with admin_client.session_transaction() as sess:
        sess['user_email'] = 'admin@example.com'

    resp = admin_client.post(f'/topics/view/{user_a_topic.topic_id}', data={
        'delete': 'احذف الموضوع',
        'topic_id': str(user_a_topic.topic_id)
    }, follow_redirects=False)

    assert resp.status_code in (301, 302)
    assert resp.headers.get('Location') == '/'
    assert Topic.get_by_id(user_a_topic.topic_id) is None
