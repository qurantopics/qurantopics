from google.cloud import ndb
from google.cloud.ndb import User
from controllers.entities import Sura, Aya, Topic, AppAdmin


def test_topic_pre_put_hook():
    topic = Topic(title="الصبر في القرآن")
    topic.put()
    assert topic.search_words == ["الصبر", "في", "القرآن"]


def test_topic_pre_put_hook_lowercase():
    topic = Topic(title="Patience in Islam")
    topic.put()
    assert topic.search_words == ["patience", "in", "islam"]


def test_sura_aya_queries(seed_data):
    sura1 = seed_data["sura1"]
    ayat = list(sura1.get_ayat_query_in_range(1, 3))
    assert len(ayat) == 3
    assert [a.number for a in ayat] == [1, 2, 3]


def test_sura_get_aya_by_number(seed_data):
    sura1 = seed_data["sura1"]
    aya = sura1.get_aya_by_number(2)
    assert aya is not None
    assert aya.number == 2
    assert "الْحَمْدُ" in aya.content

    non_existent = sura1.get_aya_by_number(99)
    assert non_existent is None


def test_aya_properties(seed_data):
    sura1 = seed_data["sura1"]
    aya = sura1.get_aya_by_number(1)
    assert aya.sura.key == sura1.key
    assert aya.sura.name == "الفاتحة"

    # Static helper test
    aya_by_static = Aya.get_by_sura_and_aya_number(1, 1)
    assert aya_by_static.key == aya.key


def test_app_admin_is_admin(seed_data):
    assert AppAdmin.is_admin("admin@example.com") is True
    assert AppAdmin.is_admin("other@example.com") is False
    assert AppAdmin.is_admin("") is False
    assert AppAdmin.is_admin(None) is False


def test_topic_get_ayat(seed_data):
    sura1 = seed_data["sura1"]
    aya1 = sura1.get_aya_by_number(1)
    aya2 = sura1.get_aya_by_number(2)

    topic = Topic(
        topic_id=101,
        title="موضوع اختبار",
        ayat_keys=[aya1.key, aya2.key],
        created_by=User(email="tester@example.com", _auth_domain="gmail.com")
    )
    topic.put()

    fetched_ayat = topic.get_ayat()
    assert len(fetched_ayat) == 2
    assert fetched_ayat[0].number == 1
    assert fetched_ayat[1].number == 2


def test_topic_remove_by_id(seed_data):
    topic = Topic(topic_id=999, title="موضوع للحذف")
    topic.put()

    assert Topic.get_by_id(999) is not None
    Topic.remove_by_id(999)
    assert Topic.get_by_id(999) is None
