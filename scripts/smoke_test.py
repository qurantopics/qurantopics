#!/usr/bin/env python3
"""
QuranTopics End-to-End Automated Smoke Test Suite (Option B)

Verifies the entire live application stack (server + Datastore emulator):
1. Public endpoints (Home, Suras List, Sura Display)
2. Mock authentication (User & Admin sessions)
3. Topic lifecycle (Add verses, save topic, view topic, search topic, delete topic)
4. Authorization & Security boundaries (Anonymous vs Owner vs Other User vs Admin)

Usage:
    python scripts/smoke_test.py [--base-url http://localhost:8080]
"""

import sys
import os
import re
import argparse
import requests
from urllib.parse import urljoin


class SmokeTestRunner:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.passed_tests = 0
        self.failed_tests = 0

    def log(self, stage: str, message: str, success: bool = True):
        status_icon = "✓" if success else "✗"
        status_text = "PASS" if success else "FAIL"
        print(f"[{status_icon} {status_text}] {stage}: {message}")
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def url(self, path: str) -> str:
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def run_all(self) -> bool:
        print(f"\n========================================================")
        print(f"  QuranTopics Smoke Test Suite")
        print(f"  Target: {self.base_url}")
        print(f"========================================================\n")

        try:
            self.test_public_home()
            self.test_public_suras_list()
            self.test_public_sura_display()
            self.test_anonymous_cannot_create_topic()
            
            created_topic_id = self.test_user_topic_lifecycle()
            
            if created_topic_id:
                self.test_user_isolation(created_topic_id)
                self.test_delete_topic(created_topic_id)

            self.test_admin_security_boundaries()

        except Exception as e:
            self.log("FATAL", f"Unexpected exception during test run: {e}", success=False)
            import traceback
            traceback.print_exc()

        print(f"\n========================================================")
        print(f"  Results: {self.passed_tests} PASSED, {self.failed_tests} FAILED")
        print(f"========================================================\n")
        return self.failed_tests == 0

    def test_public_home(self):
        resp = self.session.get(self.url("/"))
        if resp.status_code == 200 and ("الموضوعات" in resp.text or "qurantopics" in resp.text.lower() or "navbar" in resp.text):
            self.log("Public Home", f"GET / responded 200 OK")
        else:
            self.log("Public Home", f"GET / failed with status {resp.status_code}", success=False)

    def test_public_suras_list(self):
        resp = self.session.get(self.url("/list_suras"))
        if resp.status_code == 200 and ("الفاتحة" in resp.text or "البقرة" in resp.text):
            self.log("Suras List", "GET /list_suras responded 200 OK with sura names")
        else:
            self.log("Suras List", f"GET /list_suras failed or missing sura names (status {resp.status_code})", success=False)

    def test_public_sura_display(self):
        resp = self.session.get(self.url("/display_sura/1"))
        if resp.status_code == 200 and ("الفاتحة" in resp.text or "الرَّحْمَٰنِ" in resp.text or "الرحمن" in resp.text or "sura" in resp.text):
            self.log("Sura Display", "GET /display_sura/1 responded 200 OK")
        else:
            self.log("Sura Display", f"GET /display_sura/1 failed (status {resp.status_code})", success=False)

    def test_anonymous_cannot_create_topic(self):
        # Fresh unauthenticated session
        anon_session = requests.Session()
        resp = anon_session.get(self.url("/topics/add_edit"), allow_redirects=False)
        if resp.status_code in (301, 302) and "login" in resp.headers.get("Location", ""):
            self.log("Auth Boundary", "Anonymous GET /topics/add_edit correctly redirected to /login")
        else:
            self.log("Auth Boundary", f"Anonymous access expected redirect to /login, got {resp.status_code}", success=False)

    def test_user_topic_lifecycle(self) -> int:
        user_email = "tester@example.com"
        # 1. Dev mock login
        login_resp = self.session.get(self.url(f"/login?email={user_email}"), allow_redirects=True)
        if login_resp.status_code == 200 and "logout" in login_resp.text:
            self.log("User Login", f"Logged in as {user_email}")
        else:
            self.log("User Login", f"Login failed for {user_email}", success=False)

        # 2. Add verses in topic builder
        add_data = {
            "sura": "1",
            "from_aya": "1",
            "to_aya": "3",
            "add": "أضف"
        }
        resp = self.session.post(self.url("/topics/add_edit"), data=add_data)
        if resp.status_code != 200:
            self.log("Topic Builder", f"POST /topics/add_edit (add) failed with status {resp.status_code}", success=False)
            return 0

        # Extract hidden aya fields from response
        # Matches name="sura_1" value="1", name="aya_1" value="1", etc.
        hidden_inputs = re.findall(r'<input\s+name="([^"]+)"\s+(?:value="([^"]*)"\s+type="hidden"|type="hidden"\s+value="([^"]*)")', resp.text)
        
        post_data = {}
        for item in hidden_inputs:
            name = item[0]
            val = item[1] if item[1] else item[2]
            post_data[name] = val

        # Also extract position inputs if present
        pos_inputs = re.findall(r'<input\s+type="hidden"\s+name="(position_\d+)"\s+value="([^"]*)"', resp.text)
        for name, val in pos_inputs:
            post_data[name] = val

        if not any(k.startswith("aya_") for k in post_data.keys()):
            # If no verses were in DB for Sura 1, note it
            self.log("Topic Builder", "No verses returned for Sura 1 (Datastore may be unseeded). Continuing with synthetic test.", success=False)
            return 0

        # 3. Save topic
        topic_title = "موضوع تجريبي للتحقق الآلي"
        post_data["title"] = topic_title
        post_data["save"] = "احفظ الموضوع"
        save_resp = self.session.post(self.url("/topics/add_edit"), data=post_data)
        
        if save_resp.status_code == 200 and ("تم حفظ الموضوع" in save_resp.text or "topic_id" in save_resp.text):
            self.log("Topic Save", "Topic saved successfully")
        else:
            self.log("Topic Save", f"Topic save failed: {save_resp.status_code}", success=False)
            return 0

        # Extract created topic_id
        match = re.search(r'name="topic_id"\s+type="hidden"\s+value="(\d+)"', save_resp.text)
        if not match:
            match = re.search(r'value="(\d+)"\s+name="topic_id"', save_resp.text)
        
        if not match:
            self.log("Topic ID", "Could not find topic_id in save response", success=False)
            return 0

        topic_id = int(match.group(1))
        self.log("Topic ID", f"Created topic with ID: {topic_id}")

        # 4. View topic
        view_resp = self.session.get(self.url(f"/topics/view/{topic_id}"))
        if view_resp.status_code == 200 and topic_title in view_resp.text:
            self.log("Topic View", f"GET /topics/view/{topic_id} correctly rendered topic and title")
        else:
            self.log("Topic View", f"GET /topics/view/{topic_id} failed", success=False)

        # 5. Search topic
        search_resp = self.session.post(self.url("/search"), data={"search_for": "تجريبي"})
        if search_resp.status_code == 200 and str(topic_id) in search_resp.text:
            self.log("Topic Search", "POST /search found created topic")
        else:
            self.log("Topic Search", "POST /search did not find topic", success=False)

        return topic_id

    def test_user_isolation(self, topic_id: int):
        # Attacker user session
        attacker_session = requests.Session()
        attacker_session.get(self.url("/login?email=attacker@example.com"))

        # Attacker tries to delete user's topic
        delete_data = {
            "topic_id": str(topic_id),
            "delete": "احذف الموضوع"
        }
        resp = attacker_session.post(self.url(f"/topics/view/{topic_id}"), data=delete_data, allow_redirects=False)
        # Should redirect to / and NOT delete the topic
        if resp.status_code in (301, 302, 403):
            # Check if topic still exists
            check_resp = self.session.get(self.url(f"/topics/view/{topic_id}"))
            if check_resp.status_code == 200 and "تجريبي" in check_resp.text:
                self.log("Security Boundary", "Unauthorized user cannot delete another user's topic")
            else:
                self.log("Security Boundary", "Unauthorized user successfully deleted topic! VULNERABILITY!", success=False)
        else:
            self.log("Security Boundary", f"Unauthorized delete returned unexpected status {resp.status_code}", success=False)

    def test_delete_topic(self, topic_id: int):
        delete_data = {
            "topic_id": str(topic_id),
            "delete": "احذف الموضوع"
        }
        resp = self.session.post(self.url(f"/topics/view/{topic_id}"), data=delete_data, allow_redirects=True)
        if resp.status_code == 200:
            self.log("Topic Delete", f"Owner deleted topic {topic_id}")
        else:
            self.log("Topic Delete", f"Owner delete failed with status {resp.status_code}", success=False)

    def test_admin_security_boundaries(self):
        # 1. Normal user trying admin route
        normal_session = requests.Session()
        normal_session.get(self.url("/login?email=normal@example.com"))
        resp = normal_session.get(self.url("/admin/edit_aya?sura=1&aya=1"), allow_redirects=False)
        if resp.status_code in (301, 302):
            self.log("Admin Boundary", "Non-admin access to /admin/edit_aya correctly redirected")
        else:
            self.log("Admin Boundary", f"Non-admin access returned {resp.status_code} instead of redirect", success=False)

        # 2. Admin access
        admin_session = requests.Session()
        admin_session.get(self.url("/login?email=admin@example.com"))
        resp = admin_session.get(self.url("/admin/edit_aya?sura=1&aya=1"))
        if resp.status_code == 200:
            self.log("Admin Access", "Admin can access /admin/edit_aya")
        else:
            self.log("Admin Access", f"Admin access returned status {resp.status_code}", success=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QuranTopics Smoke Test Runner")
    parser.add_argument("--base-url", default=os.getenv("TEST_BASE_URL", "http://localhost:8080"), help="Base URL of QuranTopics instance")
    args = parser.parse_args()

    runner = SmokeTestRunner(base_url=args.base_url)
    success = runner.run_all()
    sys.exit(0 if success else 1)
