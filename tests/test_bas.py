import contextlib
import io

import pytest

import recon_scan
import vulnerability


class _FakeResp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _fake_recon_scan(target, *args, **kwargs):
    recon_scan.validate_scope(target)
    return {
        "target": target,
        "open_ports": [{"port": 80, "banner": ""}, {"port": 443, "banner": ""}],
        "scan_range": "1-1023",
        "status": "completed"
    }


def test_no_stdout_pollution(monkeypatch):
    monkeypatch.setattr(vulnerability, "recon_scan", _fake_recon_scan)
    monkeypatch.setattr("requests.get", lambda *a, **k: _FakeResp(200, {"port": 80, "risk_level": "LOW"}))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        vulnerability.security_assessment("192.168.137.10")

    assert buf.getvalue() == ""


def test_single_scan_call(monkeypatch):
    calls = {"count": 0}

    def counting_recon_scan(target, *args, **kwargs):
        calls["count"] += 1
        return _fake_recon_scan(target)

    monkeypatch.setattr(vulnerability, "recon_scan", counting_recon_scan)
    monkeypatch.setattr("requests.get", lambda *a, **k: _FakeResp(200, {"port": 80, "risk_level": "LOW"}))

    vulnerability.security_assessment("192.168.137.10")

    assert calls["count"] == 1


def test_out_of_scope_rejected():
    with pytest.raises(ValueError):
        recon_scan.recon_scan("8.8.8.8")

    with pytest.raises(ValueError):
        recon_scan.recon_scan("example.com")


def test_db_failure_not_silent(monkeypatch):
    monkeypatch.setattr(vulnerability, "recon_scan", _fake_recon_scan)
    monkeypatch.setattr("requests.get", lambda *a, **k: _FakeResp(500, None))

    result = vulnerability.map_vulnerabilities("192.168.137.10")

    assert result["analysis"]["db_reachable"] is False
    assert result["analysis"]["priority"] == "UNKNOWN"


def test_no_vulns_priority_none(monkeypatch):
    monkeypatch.setattr(vulnerability, "recon_scan", _fake_recon_scan)
    monkeypatch.setattr("requests.get", lambda *a, **k: _FakeResp(200, {}))

    result = vulnerability.map_vulnerabilities("192.168.137.10")

    assert result["analysis"]["db_reachable"] is True
    assert result["analysis"]["priority"] == "NONE"
