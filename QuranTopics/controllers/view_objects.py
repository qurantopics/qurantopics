
class TopicEditView():
    def __init__(self):
        self.message = None
        self.error = None
        self.topic_id = None
        self.title = ""
        self.sura = None
        self.from_aya = None
        self.to_aya = None
        self.position = None
        self.to_position = None
        self.ayat_display = []

class TopicAyaView():
    def __init__(self):
        self.position = 0
        self.selected = False
        self.sura_number = 0
        self.sura_name = ""
        self.aya_number = 0
        self.aya_content = ""
        self.aya_key = ""

class TopicLine():
    def __init__(self):
        self.new_section = False
        self.sura_number = 0
        self.sura_name = ""
        self.aya_number = 0
        self.aya_content = ""
