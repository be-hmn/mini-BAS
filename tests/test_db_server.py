import os
import sys

DB_SERVER_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db-server")
sys.path.insert(0, DB_SERVER_DIR)

import app as db_app  # noqa: E402


def test_banner_verifies_matching_cve():
    client = db_app.app.test_client()
    resp = client.get("/vulnerabilities/port/445", query_string={"banner": "Windows Server 2008 SMB"})
    data = resp.get_json()

    assert data["banner_checked"] is True
    assert any(c["confidence"] == "verified" for c in data["cve_details"])
    assert data["risk_level"] == "CRITICAL"


def test_banner_disproves_and_downgrades_risk():
    client = db_app.app.test_client()
    resp = client.get("/vulnerabilities/port/445", query_string={"banner": "Samba 4.15 on Ubuntu"})
    data = resp.get_json()

    assert data["cves"] == []
    assert data["risk_level"] == "LOW"
    assert data["exploitable"] is False


def test_no_banner_stays_unverified():
    client = db_app.app.test_client()
    resp = client.get("/vulnerabilities/port/445")
    data = resp.get_json()

    assert data["banner_checked"] is False
    assert all(c["confidence"] == "unverified" for c in data["cve_details"])
    assert data["risk_level"] == "CRITICAL"
