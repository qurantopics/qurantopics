import pytest
from controllers.view_objects import TopicEditView, TopicAyaView, TopicLine
from controllers.view_topic import ViewTopic
from controllers.create_or_edit_topic import CreateOrEditTopic
from controllers.entities import Sura, Aya


from types import SimpleNamespace

def create_mock_aya(sura_num, sura_name, aya_num, content="نص"):
    return SimpleNamespace(
        sura=SimpleNamespace(number=sura_num, name=sura_name),
        number=aya_num,
        content=content
    )


def test_make_topic_lines_consecutive():
    vt = ViewTopic()
    ayat = [
        create_mock_aya(1, "الفاتحة", 1),
        create_mock_aya(1, "الفاتحة", 2),
        create_mock_aya(1, "الفاتحة", 3),
    ]
    lines = vt.make_topic_lines(ayat)
    assert len(lines) == 3
    assert lines[0].new_section is True
    assert lines[1].new_section is False
    assert lines[2].new_section is False


def test_make_topic_lines_discontinuous():
    vt = ViewTopic()
    ayat = [
        create_mock_aya(1, "الفاتحة", 1),
        create_mock_aya(1, "الفاتحة", 5),
    ]
    lines = vt.make_topic_lines(ayat)
    assert len(lines) == 2
    assert lines[0].new_section is True
    assert lines[1].new_section is True


def test_make_topic_lines_different_suras():
    vt = ViewTopic()
    ayat = [
        create_mock_aya(1, "الفاتحة", 7),
        create_mock_aya(112, "الإخلاص", 1),
    ]
    lines = vt.make_topic_lines(ayat)
    assert len(lines) == 2
    assert lines[0].new_section is True
    assert lines[1].new_section is True


def test_topic_edit_deduplication():
    controller = CreateOrEditTopic()
    aya1 = TopicAyaView()
    aya1.sura_number = 1
    aya1.aya_number = 2

    aya2 = TopicAyaView()
    aya2.sura_number = 1
    aya2.aya_number = 2

    aya3 = TopicAyaView()
    aya3.sura_number = 1
    aya3.aya_number = 3

    assert controller.same_aya(aya1, aya2) is True
    assert controller.same_aya(aya1, aya3) is False
    assert controller.list_contains_aya([aya1], aya2) is True
    assert controller.list_contains_aya([aya1], aya3) is False


def test_topic_edit_positional_insert():
    controller = CreateOrEditTopic()
    controller.topic_edit_view = TopicEditView()

    a1 = TopicAyaView()
    a1.sura_number = 1
    a1.aya_number = 1

    a2 = TopicAyaView()
    a2.sura_number = 1
    a2.aya_number = 2

    a3 = TopicAyaView()
    a3.sura_number = 1
    a3.aya_number = 3

    controller.topic_edit_view.ayat_display = [a1, a3]
    # Insert a2 at position 2 (1-based)
    controller.topic_edit_view.position = 2
    controller.merge_added_ayat_to_topic_ayat([a2])

    result = controller.topic_edit_view.ayat_display
    assert len(result) == 3
    assert [a.aya_number for a in result] == [1, 2, 3]


def test_topic_edit_append_when_no_position():
    controller = CreateOrEditTopic()
    controller.topic_edit_view = TopicEditView()

    a1 = TopicAyaView()
    a1.sura_number = 1
    a1.aya_number = 1

    a2 = TopicAyaView()
    a2.sura_number = 1
    a2.aya_number = 2

    controller.topic_edit_view.ayat_display = [a1]
    controller.topic_edit_view.position = None
    controller.merge_added_ayat_to_topic_ayat([a2])

    result = controller.topic_edit_view.ayat_display
    assert len(result) == 2
    assert [a.aya_number for a in result] == [1, 2]


def test_topic_edit_reordering():
    controller = CreateOrEditTopic()
    controller.topic_edit_view = TopicEditView()

    a1 = TopicAyaView()
    a1.sura_number = 1
    a1.aya_number = 1

    a2 = TopicAyaView()
    a2.sura_number = 1
    a2.aya_number = 2

    a3 = TopicAyaView()
    a3.sura_number = 1
    a3.aya_number = 3
    a3.selected = True  # Select a3 to move to position 1

    controller.topic_edit_view.ayat_display = [a1, a2, a3]
    controller.topic_edit_view.to_position = 1
    controller.move_selected_to_position()

    result = controller.topic_edit_view.ayat_display
    assert [a.aya_number for a in result] == [3, 1, 2]


def test_topic_edit_remove_selected():
    controller = CreateOrEditTopic()
    controller.topic_edit_view = TopicEditView()

    a1 = TopicAyaView()
    a1.sura_number = 1
    a1.aya_number = 1

    a2 = TopicAyaView()
    a2.sura_number = 1
    a2.aya_number = 2
    a2.selected = True

    controller.topic_edit_view.ayat_display = [a1, a2]
    controller.remove_selected()

    assert len(controller.topic_edit_view.ayat_display) == 1
    assert controller.topic_edit_view.ayat_display[0].aya_number == 1
