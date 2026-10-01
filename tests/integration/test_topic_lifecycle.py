import re
import pytest
from controllers.entities import Topic, Sura, Aya
from google.cloud.ndb import User


def test_create_topic_requires_login_get(client):
    resp = client.get('/topics/add_edit', follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "login" in resp.headers.get('Location', '')


def test_create_topic_requires_login_post(client):
    resp = client.post('/topics/add_edit', data={'save': 'احفظ الموضوع'}, follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "login" in resp.headers.get('Location', '')


def test_create_topic_validation_empty_title(user_client, seed_data):
    # Missing title with empty ayat
    resp = user_client.post('/topics/add_edit', data={'save': 'احفظ الموضوع'})
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "لم يتم إدخال عنوان الموضوع" in html


def test_create_topic_validation_empty_ayat(user_client, seed_data):
    # Title provided but no ayat
    resp = user_client.post('/topics/add_edit', data={
        'save': 'احفظ الموضوع',
        'title': 'موضوع بدون آيات'
    })
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "الموضوع لا يتضمن أي آيات" in html


def test_add_ayat_validation_invalid_input(user_client):
    resp = user_client.post('/topics/add_edit', data={
        'add': 'أضف',
        'sura': '',
        'from_aya': ''
    })
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "لم يتم ادخال رقم السورة أو الآية بصورة صحيحة" in html


def test_topic_full_lifecycle(user_client, seed_data):
    # 1. Add verses (Sura 1, Ayat 1 to 3)
    resp = user_client.post('/topics/add_edit', data={
        'add': 'أضف',
        'sura': '1',
        'from_aya': '1',
        'to_aya': '3'
    })
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ" in html

    # Extract hidden inputs for saving
    inputs = re.findall(r'<input\s+name="([^"]+)"\s+(?:value="([^"]*)"\s+type="hidden"|type="hidden"\s+value="([^"]*)")', html)
    post_data = {}
    for name, v1, v2 in inputs:
        post_data[name] = v1 if v1 else v2

    pos_inputs = re.findall(r'<input\s+type="hidden"\s+name="(position_\d+)"\s+value="([^"]*)"', html)
    for name, val in pos_inputs:
        post_data[name] = val

    # 2. Save topic
    topic_title = "موضوع متكامل للاختبار"
    post_data['title'] = topic_title
    post_data['save'] = 'احفظ الموضوع'

    save_resp = user_client.post('/topics/add_edit', data=post_data)
    assert save_resp.status_code == 200
    save_html = save_resp.data.decode('utf-8')
    assert "تم حفظ الموضوع" in save_html

    # Extract topic_id
    id_match = re.search(r'name="topic_id"\s+type="hidden"\s+value="(\d+)"', save_html)
    if not id_match:
        id_match = re.search(r'value="(\d+)"\s+name="topic_id"', save_html)
    assert id_match is not None
    topic_id = int(id_match.group(1))

    # Verify entity in Datastore
    topic = Topic.get_by_id(topic_id)
    assert topic is not None
    assert topic.title == topic_title
    assert len(topic.ayat_keys) == 3

    # 3. View topic
    view_resp = user_client.get(f'/topics/view/{topic_id}')
    assert view_resp.status_code == 200
    view_html = view_resp.data.decode('utf-8')
    assert topic_title in view_html
    assert "عدل الموضوع" in view_html
    assert "احذف الموضوع" in view_html

    # 4. Edit existing topic (change title)
    updated_title = "موضوع متكامل معدل"
    post_data['topic_id'] = str(topic_id)
    post_data['title'] = updated_title
    post_data['save'] = 'احفظ الموضوع'

    edit_resp = user_client.post('/topics/add_edit', data=post_data)
    assert edit_resp.status_code == 200
    updated_topic = Topic.get_by_id(topic_id)
    assert updated_topic.title == updated_title

    # 5. Delete topic
    delete_resp = user_client.post(f'/topics/view/{topic_id}', data={
        'topic_id': str(topic_id),
        'delete': 'احذف الموضوع'
    }, follow_redirects=False)

    assert delete_resp.status_code in (301, 302)
    assert delete_resp.headers.get('Location') == '/'

    # Verify deleted from Datastore
    assert Topic.get_by_id(topic_id) is None
