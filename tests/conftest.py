import os
import sys
import socket
import subprocess
import time
import pytest

# Set emulator environment variables before importing app or ndb
os.environ.setdefault("DATASTORE_EMULATOR_HOST", "localhost:8081")
os.environ.setdefault("APPLICATION_ID", "dev~qurantopics")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "qurantopics")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from google.cloud import ndb as cloud_ndb
from main import app as flask_app
from controllers.entities import Sura, Aya, Topic, AppAdmin


def is_emulator_listening(host="127.0.0.1", port=8081):
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except (OSError, ConnectionRefusedError):
        return False


@pytest.fixture(scope="session", autouse=True)
def ensure_datastore_emulator():
    host_port = os.environ.get("DATASTORE_EMULATOR_HOST", "localhost:8081")
    parts = host_port.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 8081

    proc = None
    if not is_emulator_listening(host, port):
        # Attempt to start the datastore emulator using gcloud
        gcloud_bin = None
        candidate = "/home/tabdelmaguid/Downloads/google-cloud-cli/google-cloud-sdk/bin/gcloud"
        if os.path.exists(candidate):
            gcloud_bin = candidate
        else:
            import shutil
            gcloud_bin = shutil.which("gcloud")

        if gcloud_bin:
            cmd = [
                gcloud_bin, "beta", "emulators", "datastore", "start",
                f"--host-port={host}:{port}",
                "--no-store-on-disk",
                "--consistency=1.0"
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Wait up to 10 seconds for emulator to start
            for _ in range(20):
                time.sleep(0.5)
                if is_emulator_listening(host, port):
                    break

    yield

    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def ndb_client():
    client = cloud_ndb.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "qurantopics"))
    return client


@pytest.fixture(autouse=True)
def clean_and_context(ndb_client):
    """Ensure an active NDB context for every test, and clean up test entities."""
    with ndb_client.context():
        yield
        # Delete any test topics created during tests to keep them isolated
        topic_keys = Topic.query().fetch(keys_only=True)
        if topic_keys:
            cloud_ndb.delete_multi(topic_keys)


@pytest.fixture
def seed_data():
    """Seed Sura 1, Sura 112, their Ayat, and AppAdmin."""
    # Check if Sura 1 already exists
    sura1 = Sura.query(Sura.number == 1).get()
    if not sura1:
        sura1 = Sura(number=1, name="الفاتحة", number_of_ayat=7)
        sura1.put()

        fatiha_verses = [
            (1, "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"),
            (2, "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"),
            (3, "الرَّحْمَٰنِ الرَّحِيمِ"),
            (4, "مَالِكِ يَوْمِ الدِّينِ"),
            (5, "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ"),
            (6, "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ"),
            (7, "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ"),
        ]
        for num, text in fatiha_verses:
            aya = Aya(sura_key=sura1.key, number=num, content=text)
            aya.put()

    sura112 = Sura.query(Sura.number == 112).get()
    if not sura112:
        sura112 = Sura(number=112, name="الإخلاص", number_of_ayat=4)
        sura112.put()

        ikhlas_verses = [
            (1, "قُلْ هُوَ اللَّهُ أَحَدٌ"),
            (2, "اللَّهُ الصَّمَدُ"),
            (3, "لَمْ يَلِدْ وَلَمْ يُولَدْ"),
            (4, "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ"),
        ]
        for num, text in ikhlas_verses:
            aya = Aya(sura_key=sura112.key, number=num, content=text)
            aya.put()

    admin = AppAdmin.query(AppAdmin.email == "admin@example.com").get()
    if not admin:
        admin = AppAdmin(email="admin@example.com")
        admin.put()

    return {
        "sura1": sura1,
        "sura112": sura112,
        "admin": admin
    }



@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key"
    })
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_client(app):
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess['user_email'] = 'user@example.com'
    return test_client


@pytest.fixture
def admin_client(app, seed_data):
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess['user_email'] = 'admin@example.com'
    return test_client
