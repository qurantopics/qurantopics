import pytest
from controllers.entities import Topic, Sura, Aya
from google.cloud.ndb import User


def test_main_page_empty(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert "مواضيع القرآن الكريم" in resp.data.decode('utf-8')


def test_main_page_with_topics(client):
    topic = Topic(topic_id=1, title="موضوع تجريبي عام")
    topic.put()

    resp = client.get('/')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "موضوع تجريبي عام" in html
    assert "/topics/view/1" in html


def test_suras_list(client, seed_data):
    resp = client.get('/list_suras')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "الفاتحة" in html
    assert "الإخلاص" in html


def test_display_sura(client, seed_data):
    resp = client.get('/display_sura/1')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "الفاتحة" in html
    assert "الرَّحْمَٰنِ الرَّحِيمِ" in html
    assert "﴿7﴾" in html


def test_display_nonexistent_sura(client):
    resp = client.get('/display_sura/999')
    assert resp.status_code == 200


def test_search_topics_matching(client):
    topic1 = Topic(topic_id=10, title="الصبر والتقوى")
    topic1.put()
    topic2 = Topic(topic_id=20, title="الصلاة والزكاة")
    topic2.put()

    resp = client.post('/search', data={'search_for': 'الصبر'})
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "الصبر والتقوى" in html
    assert "الصلاة والزكاة" not in html


def test_search_topics_non_matching(client):
    topic = Topic(topic_id=30, title="الجهاد والشهادة")
    topic.put()

    resp = client.post('/search', data={'search_for': 'الإنفاق'})
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "الجهاد والشهادة" not in html


def test_search_get_redirects_to_home(client):
    resp = client.get('/search')
    assert resp.status_code in (301, 302)
    assert resp.headers.get('Location') == '/'


def test_about_page(client):
    resp = client.get('/about')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "مرحبا بكم في موقع مواضيع القرآن الكريم" in html
    assert "عن الموقع" in html
