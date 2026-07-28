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


@app.route("/vulnerabilities/port/<int:port>", methods=["GET"])
def get_port_vulnerabilities(port):
    """포트별 취약점 조회"""
    port_str = str(port)

    port_info = PORTS.get("services", {}).get(port_str)
    mapping = MAPPINGS.get("port_to_cve", {}).get(port_str)

    if not mapping:
        return jsonify({"error": "Port not found"}), 404

    vuln_data = {
        "port": port,
        "service": mapping.get("service"),
        "protocol": port_info.get("protocol") if port_info else "Unknown",
        "cves": mapping.get("cves", []),
        "risk_level": mapping.get("risk_level"),
        "exploitable": len(mapping.get("cves", [])) > 0,
        "attack_vectors": []
    }

    # CVE 상세 정보
    cve_details = []
    for cve in vuln_data["cves"]:
        cve_info = CVES.get("cves", {}).get(cve)
        if cve_info:
            cve_details.append({
                "cve_id": cve,
                "title": cve_info.get("title"),
                "severity": cve_info.get("severity"),
                "cvss_score": cve_info.get("cvss_score"),
                "exploit_type": cve_info.get("exploit_type")
            })
            if cve_info.get("exploit_type") not in vuln_data["attack_vectors"]:
                vuln_data["attack_vectors"].append(cve_info.get("exploit_type"))

    vuln_data["cve_details"] = cve_details
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
