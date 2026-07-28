# BAS

> **Model Context Protocol(MCP) 기반 Breach and Attack Simulation(BAS) Tool**

## 프로젝트 소개

**BAS**는 네트워크 스캐닝과 취약점 조회를 자동화하여 **Claude Desktop**에서 보안 진단을 수행하는 MCP 기반 프로젝트입니다.

Claude Desktop이 **MCP Client**로 동작하며 `bas_mcp_server.py`에 등록된 MCP Tool(`recon`, `map_vulnerabilities`, `security_assessment`)을 직접 호출합니다. 서버는 대상 시스템의 열린 포트를 탐지하고, Docker로 구동되는 취약점 데이터베이스(db-server)에서 관련 취약점을 조회한 뒤 결과를 JSON으로 반환합니다. 위험도, 공격 가능성, 대응 방안에 대한 최종 분석은 프로젝트 내부가 아닌 **Claude Desktop이 자연어로 수행**합니다.

대상은 환경변수 `LAB_SCOPE`로 지정한 격리된 랩 네트워크의 IP 리터럴로 코드 레벨에서 강제됩니다. 호스트명 입력은 허용되지 않습니다.

본 프로젝트는 실제 공격을 수행하기 위한 도구가 아닌 **교육, 연구 및 허가된 환경에서의 보안 진단**을 목적으로 개발되었습니다.

---

## 주요 기능

* TCP 기반 포트 스캐닝
* 서비스 및 포트 정보 수집
* Docker 기반 취약점 데이터 조회
* MCP(Model Context Protocol) 서버 제공 (recon / map_vulnerabilities / security_assessment)
* 대상 스코프 검증 (LAB_SCOPE 기반)
* Claude Desktop 연동 (MCP Client)

---

## 시연 영상

https://github.com/user-attachments/assets/8da66ccb-3f15-4aa5-935f-1870196843e1

---

## 시스템 구조

```text
                Claude Desktop
                 (MCP Client)
                       │
                       ▼
              bas_mcp_server.py
        (recon / map_vulnerabilities /
           security_assessment)
                       │
                       ▼
              vulnerability.py
          (스코프 검증은 recon_scan.py)
                 │            │
                 │            ▼
                 │     Docker DB Server
                 │       (REST API)
                 ▼
            recon_scan.py
        (LAB_SCOPE 검증 + 포트 스캔)
                 │
                 ▼
         취약점 정보 반환(JSON)
                 │
                 ▼
      Claude Desktop이 결과를 분석하여 사용자에게 제공
```

---

## MCP 도구

| 도구 | 입력 | 출력 | 용도 |
| --- | --- | --- | --- |
| `recon` | `target` (IPv4) | `{phase, target, result: {open_ports: [{port, banner}], scan_range, status}}` | 포트 스캔 + 서비스 배너 수집 |
| `map_vulnerabilities` | `target` (IPv4), `open_ports`(선택, `[{port, banner}]`) | `{phase, target, scan_result, analysis: {vulnerabilities, priority, recommended_path, total_vulnerable_ports, db_reachable, errors, partial}}` | 포트+배너→CVE 매핑. `open_ports`가 주어지면 재스캔하지 않음 |
| `security_assessment` | `target` (IPv4) | `{target, timestamp, scan_result, vulnerability_analysis, summary}` | `recon` + `map_vulnerabilities`를 순차 실행하는 복합 도구 (스캔은 1회만 수행) |

모든 도구는 격리된 랩 환경(`LAB_SCOPE`)의 소유 장비만을 대상으로 하며, 스코프를 벗어난 요청은 스캔 시작 전 `{"error": "...", "code": "OUT_OF_SCOPE"}`로 거부됩니다.

`priority`는 다음 값 중 하나입니다:

| priority | 의미 |
| --- | --- |
| `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` | 매칭된 취약점 중 최고 위험도 |
| `NONE` | DB 조회는 정상이나 매칭된 취약점 없음 |
| `UNKNOWN` | 열린 포트에 대한 DB 조회가 전부 실패 — 판정 불가 |

### 취약점 신뢰도 (confidence)

포트 번호만으로 CVE를 단정하지 않기 위해, `recon`이 수집한 서비스 배너를 DB 조회 시 함께 전달합니다. 배너와 CVE의 `affected_versions`를 대조한 결과에 따라 `cve_details[].confidence`가 결정됩니다.

| confidence | 조건 | 의미 |
| --- | --- | --- |
| `verified` | 배너가 있고 `affected_versions`와 일치 | 실제 취약 버전으로 확인됨 |
| `unverified` | 배너를 얻지 못함 (예: SMB처럼 핸드셰이크 없이는 응답 안 하는 서비스) | 포트 기반 추정치, 버전 미확인 |
| (제외) | 배너가 있는데 `affected_versions`와 불일치 | 해당 CVE는 결과에서 제외되고, 포트의 알려진 CVE가 모두 제외되면 `risk_level`이 `LOW`로 하향 조정됨 |

SSH, FTP, HTTP처럼 연결 즉시 배너를 보내는 서비스는 `verified`/제외로 판정되지만, SMB(445)처럼 클라이언트 요청 없이는 배너를 안 주는 서비스는 여전히 `unverified`로 남습니다 — 이는 버그가 아니라 실제로 검증할 수 없다는 정직한 표시입니다.

---

## 프로젝트 구조

```text
BAS/
│
├── bas_mcp_server.py          # MCP 서버 (recon / map_vulnerabilities / security_assessment)
├── vulnerability.py           # 보안 진단 도구 (scan / map_vulnerabilities / security_assessment)
├── recon_scan.py              # TCP 포트 스캐너 + LAB_SCOPE 검증
│
├── tests/                      # pytest (네트워크 접근 없이 monkeypatch로 검증)
│
├── db-server/
│   ├── app.py                 # 취약점 조회 API
│   ├── Dockerfile
│   ├── requirements.txt
│   └── data/
│       ├── cves.json
│       ├── mappings.json
│       └── ports.json
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 기술 스택

| 분야        | 기술                           |
| --------- | ---------------------------- |
| Language  | Python                       |
| Protocol  | Model Context Protocol (MCP) |
| Database  | JSON 기반 취약점 데이터              |
| Container | Docker                       |
| API       | REST API (Flask)             |

---

## 설치 방법

### Python 패키지 설치

```bash
pip install -r requirements.txt
```

---

## 환경변수

`.env.example`을 `.env`로 복사한 뒤 값을 채웁니다.

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `DB_URL` | `http://127.0.0.1:5000` | 취약점 조회 REST API 서버 주소 |
| `LAB_SCOPE` | `192.168.137.0/24` | 스캔이 허용되는 CIDR 목록 (콤마로 구분해 여러 대역 지정 가능) |
| `SCAN_THREADS` | `64` | 포트 스캔 스레드 수 (상한 256으로 클램프) |

---

## Docker 데이터베이스 실행

```bash
cd db-server
docker compose up --build
```

---

## MCP 서버 실행

```bash
python bas_mcp_server.py
```

이후 Claude Desktop의 MCP 설정에 `bas_mcp_server.py`를 등록하면 보안 진단 도구를 사용할 수 있습니다.

---

## 동작 과정

```text
대상 시스템 입력 (IP 리터럴)
        │
        ▼
LAB_SCOPE 스코프 검증
        │
        ▼
포트 스캔 + 배너 수집 (recon)
        │
        ▼
배너 기반 취약점 데이터 조회 (map_vulnerabilities)
        │
        ▼
MCP를 통해 Claude Desktop으로 결과 전달
        │
        ▼
Claude Desktop이 위험도 및 대응 방안 분석
        │
        ▼
최종 분석 결과 제공
```

---

## 취약점 데이터

취약점 데이터는 `db-server/data/` 디렉터리에서 JSON 형식으로 관리됩니다.

| 파일              | 설명             |
| --------------- | -------------- |
| `cves.json`     | CVE 및 취약점 정보   |
| `mappings.json` | 서비스와 취약점 매핑 정보 |
| `ports.json`    | 서비스 및 기본 포트 정보 |

JSON 파일을 수정하여 새로운 취약점 또는 서비스를 추가할 수 있습니다.

---

## 테스트

```bash
pytest tests/ -v
```

네트워크 접근 없이 `recon_scan`과 `requests.get`을 monkeypatch로 대체해 검증합니다.

---

## 주의사항

본 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

허가받지 않은 시스템에 대한 스캐닝이나 보안 테스트는 관련 법률을 위반할 수 있으므로 반드시 적법한 환경에서만 사용해야 합니다.

스코프 검증은 코드 레벨(`recon_scan.validate_scope`)로 강제되며, `LAB_SCOPE` 대역을 벗어난 IP나 호스트명 입력은 스캔 시작 전에 거부됩니다.
