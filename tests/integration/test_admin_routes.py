import pytest
from controllers.entities import Sura, Aya, Topic
from google.cloud import ndb


def test_non_admin_cannot_access_edit_aya(user_client):
    resp = user_client.get('/admin/edit_aya?sura=1&aya=1', follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert resp.headers.get('Location') == '/'


def test_anonymous_cannot_access_edit_aya(client):
    resp = client.get('/admin/edit_aya?sura=1&aya=1', follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "login" in resp.headers.get('Location', '')


def test_admin_edit_aya_get(admin_client, seed_data):
    resp = admin_client.get('/admin/edit_aya?sura=1&aya=1')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert "الرَّحِيمِ" in html


def test_admin_edit_aya_post_modify_content(admin_client, seed_data):
    sura1 = seed_data["sura1"]
    aya = sura1.get_aya_by_number(1)
    aya_key_str = aya.key.urlsafe().decode('utf-8')

    new_content = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ (معدل)"
    resp = admin_client.post('/admin/edit_aya', data={
        'edit': 'تعديل',
        'aya_key': aya_key_str,
        'aya_content': new_content
    })
    assert resp.status_code == 200

    refreshed_aya = aya.key.get()
    assert refreshed_aya.content == new_content

    # Revert back to original content
    refreshed_aya.content = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    refreshed_aya.put()


def test_admin_delete_aya_prevented_if_used_in_topic(admin_client, seed_data):
    sura1 = seed_data["sura1"]
    aya = sura1.get_aya_by_number(3)
    aya_key_str = aya.key.urlsafe().decode('utf-8')

    # Associate aya with a topic
    topic = Topic(topic_id=777, title="موضوع مرتبط بآية", ayat_keys=[aya.key])
    topic.put()

    # Admin attempts to delete this aya
    resp = admin_client.post('/admin/edit_aya', data={
        'delete': 'حذف',
        'aya_key': aya_key_str
    })
    assert resp.status_code == 200

    # Aya must NOT be deleted because it is referenced in a topic
    assert aya.key.get() is not None


def test_admin_reput_sura(admin_client, seed_data):
    resp = admin_client.get('/admin/reput_sura?sura=1')
    assert resp.status_code == 200
    assert "reput num of ayat: 7" in resp.data.decode('utf-8')
