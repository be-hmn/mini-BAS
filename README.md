# BAS

> **Model Context Protocol(MCP) 기반 Breach and Attack Simulation(BAS) Tool**

## 프로젝트 소개

**BAS**는 네트워크 스캐닝과 취약점 조회를 자동화하여 **Claude Desktop**에서 보안 진단을 수행하는 MCP 기반 프로젝트입니다.

Claude Desktop이 **MCP Client**로 동작하며 `bas_mcp_server.py`에 등록된 MCP Tool을 직접 호출합니다. 서버는 대상 시스템의 열린 포트를 탐지하고, Docker로 구동되는 취약점 데이터베이스(db-server)에서 관련 취약점을 조회한 뒤 결과를 JSON으로 반환합니다. 위험도, 공격 가능성, 대응 방안에 대한 최종 분석은 프로젝트 내부가 아닌 **Claude Desktop이 자연어로 수행**합니다.

본 프로젝트는 실제 공격을 수행하기 위한 도구가 아닌 **교육, 연구 및 허가된 환경에서의 보안 진단**을 목적으로 개발되었습니다.

---

## 주요 기능

* TCP 기반 포트 스캐닝
* 서비스 및 포트 정보 수집
* Docker 기반 취약점 데이터 조회
* MCP(Model Context Protocol) 서버 제공
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
                       │
                       ▼
              vulnerability.py
                 │            │
                 │            ▼
                 │     Docker DB Server
                 │
                 ▼
            recon_scan.py
                 │
                 ▼
         취약점 정보 반환(JSON)
                 │
                 ▼
      Claude Desktop이 결과를 분석하여 사용자에게 제공
```

---

## 프로젝트 구조

```text
BAS/
│
├── bas_mcp_server.py          # MCP 서버
├── vulnerability.py           # 보안 진단 도구
├── recon_scan.py              # TCP 포트 스캐너
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
대상 시스템 입력
        │
        ▼
포트 스캔
        │
        ▼
서비스 식별
        │
        ▼
취약점 데이터 조회
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

## 주의사항

본 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

허가받지 않은 시스템에 대한 스캐닝이나 보안 테스트는 관련 법률을 위반할 수 있으므로 반드시 적법한 환경에서만 사용해야 합니다.
