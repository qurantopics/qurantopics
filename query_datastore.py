import os
from google.cloud import ndb

os.environ["DATASTORE_EMULATOR_HOST"] = "localhost:8081"
# We need to know what project ID we are using
client = ndb.Client(project="qurantopics")
with client.context():
    print(ndb.Model._get_kind())
