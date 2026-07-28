"""
Vulnerability DB REST API Server
"""

from flask import Flask, jsonify, request
import json
from pathlib import Path

app = Flask(__name__)

# DB 로드
DB_DIR = Path(__file__).parent / "data"

def load_dbs():
    """JSON DB 로드"""
    with open(DB_DIR / "mappings.json", "r", encoding="utf-8") as f:
        mappings = json.load(f)
    with open(DB_DIR / "cves.json", "r", encoding="utf-8") as f:
        cves = json.load(f)
    with open(DB_DIR / "ports.json", "r", encoding="utf-8") as f:
        ports = json.load(f)
    return mappings, cves, ports

MAPPINGS, CVES, PORTS = load_dbs()


@app.route("/health", methods=["GET"])
def health():
    """헬스 체크"""
    return jsonify({"status": "ok"}), 200


def _version_matches(banner: str, affected_versions: list) -> bool:
    """배너 문자열에 취약 버전 키워드가 등장하는지 대소문자 무시하고 확인."""
    banner_lower = banner.lower()
    return any(v.lower() in banner_lower for v in affected_versions)


@app.route("/vulnerabilities/port/<int:port>", methods=["GET"])
def get_port_vulnerabilities(port):
    """포트+배너 기반 취약점 조회.

    banner 쿼리 파라미터가 있으면 CVE의 affected_versions와 대조해
    실제로 해당 버전인 CVE만 confidence="verified"로 남기고
    나머지는 제외한다(단정 대신 근거 기반 판정).
    banner가 없으면 기존처럼 포트 매핑만으로 confidence="unverified"를 부여한다.
    """
    port_str = str(port)
    banner = request.args.get("banner", "").strip()

    port_info = PORTS.get("services", {}).get(port_str)
    mapping = MAPPINGS.get("port_to_cve", {}).get(port_str)

    if not mapping:
        return jsonify({"error": "Port not found"}), 404

    cve_details = []
    matched_cves = []
    attack_vectors = []

    for cve in mapping.get("cves", []):
        cve_info = CVES.get("cves", {}).get(cve)
        if not cve_info:
            continue

        affected_versions = cve_info.get("affected_versions", [])
        if banner:
            if not _version_matches(banner, affected_versions):
                continue
            confidence = "verified"
        else:
            confidence = "unverified"

        matched_cves.append(cve)
        cve_details.append({
            "cve_id": cve,
            "title": cve_info.get("title"),
            "severity": cve_info.get("severity"),
            "cvss_score": cve_info.get("cvss_score"),
            "exploit_type": cve_info.get("exploit_type"),
            "affected_versions": affected_versions,
            "confidence": confidence
        })
        if cve_info.get("exploit_type") not in attack_vectors:
            attack_vectors.append(cve_info.get("exploit_type"))

    # banner로 취약 버전이 아님이 확인되면(원래 CVE가 있었는데 하나도 매칭 안 됨) risk 하향
    if banner and mapping.get("cves") and not matched_cves:
        risk_level = "LOW"
    else:
        risk_level = mapping.get("risk_level")

    vuln_data = {
        "port": port,
        "service": mapping.get("service"),
        "protocol": port_info.get("protocol") if port_info else "Unknown",
        "banner_checked": bool(banner),
        "cves": matched_cves,
        "cve_details": cve_details,
        "risk_level": risk_level,
        "exploitable": len(matched_cves) > 0,
        "attack_vectors": attack_vectors
    }

    return jsonify(vuln_data), 200


@app.route("/vulnerabilities/batch", methods=["POST"])
def get_batch_vulnerabilities():
    """포트 리스트 일괄 조회"""
    data = request.get_json()
    ports = data.get("ports", [])

    results = []
    for port in ports:
        port_str = str(port)
        mapping = MAPPINGS.get("port_to_cve", {}).get(port_str)

        if mapping:
            results.append({
                "port": port,
                "service": mapping.get("service"),
                "risk_level": mapping.get("risk_level"),
                "cves": mapping.get("cves", [])
            })

    return jsonify({"vulnerabilities": results}), 200


@app.route("/cve/<cve_id>", methods=["GET"])
def get_cve_details(cve_id):
    """CVE 상세 정보 조회"""
    cve_info = CVES.get("cves", {}).get(cve_id)

    if not cve_info:
        return jsonify({"error": "CVE not found"}), 404

    return jsonify({
        "cve_id": cve_id,
        **cve_info
    }), 200


@app.route("/db/stats", methods=["GET"])
def get_db_stats():
    """DB 통계"""
    total_ports = len(MAPPINGS.get("port_to_cve", {}))
    total_cves = len(CVES.get("cves", {}))
    vulnerable_ports = sum(1 for p in MAPPINGS.get("port_to_cve", {}).values() if p.get("cves"))

    return jsonify({
        "total_ports": total_ports,
        "total_cves": total_cves,
        "vulnerable_ports": vulnerable_ports
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
