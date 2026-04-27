from google.cloud import ndb

class Sura(ndb.Model):
    number = ndb.IntegerProperty()
    name = ndb.StringProperty()
    number_of_ayat = ndb.IntegerProperty()
    
    @property
    def aya_set(self):
        return Aya.query(Aya.sura_key == self.key)
        
    @staticmethod
    def get_by_number(sura_number):
        return Sura.query(Sura.number == sura_number).get()
    
    def get_ayat_query_in_range(self, from_aya, to_aya):
        ayat = self.aya_set
        ayat = ayat.filter(Aya.number >= from_aya)
        ayat = ayat.filter(Aya.number <= to_aya)
        ayat = ayat.order(Aya.number)
        return ayat

    def get_aya_by_number(self, aya_number):
        ayat = self.aya_set
        ayat = ayat.filter(Aya.number == aya_number)
        return ayat.get()

  
class Aya(ndb.Model):
    # Backward compatible definition: Datastore name is 'sura'
    # Actually, old db.ReferenceProperty used the property name.
    sura_key = ndb.KeyProperty(kind='Sura', name='sura') 
    number = ndb.IntegerProperty()
    content = ndb.TextProperty()
    
    @property
    def sura(self):
        if not getattr(self, '_sura', None):
            self._sura = self.sura_key.get()
        return self._sura
    
    @staticmethod
    def get_by_sura_and_aya_number(sura_number, aya_number):
        sura = Sura.get_by_number(sura_number)
        return sura.get_aya_by_number(aya_number)


class Topic(ndb.Model):
    topic_id = ndb.IntegerProperty()
    title = ndb.StringProperty()
    ayat_keys = ndb.KeyProperty(repeated=True)
    created_by = ndb.UserProperty()
    # Adding a simple search capability for title words
    search_words = ndb.StringProperty(repeated=True)
    
    def _pre_put_hook(self):
        if self.title:
            self.search_words = [w.lower() for w in self.title.split()]
    
    @staticmethod
    def get_by_id(topic_id):
        return Topic.query(Topic.topic_id == topic_id).get()

    @staticmethod
    def remove_by_id(topic_id):
        topic = Topic.get_by_id(topic_id)
        if topic:
            topic.key.delete()

    @staticmethod
    def delete(topic):
        topic.key.delete()
    
    def get_ayat(self):
        return ndb.get_multi(self.ayat_keys)


