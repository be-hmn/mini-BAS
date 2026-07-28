# mini-BAS

> **Model Context Protocol(MCP)과 Claude Desktop을 활용한 경량 Breach and Attack Simulation(BAS) 프레임워크**

## 프로젝트 소개

**MCP를 통해 수집된 취약점 정보를 Claude Desktop에 전달하고, Claude Chat이 결과를 분석하여 위험도와 대응 방안을 제공합니다.

대상 시스템의 포트를 스캔하여 실행 중인 서비스를 식별하고, Docker 기반 취약점 데이터베이스를 통해 관련 취약점을 조회합니다. 조회된 결과는 **MCP(Model Context Protocol)**를 통해 Claude Desktop으로 전달되며, Claude가 취약점의 위험도와 공격 가능성, 대응 방안을 분석하여 사용자에게 제공합니다.

본 프로젝트는 실제 공격을 수행하기 위한 도구가 아닌 **보안 진단 및 교육·연구 목적의 BAS 시스템**을 목표로 개발되었습니다.

---

## 주요 기능

* TCP 기반 네트워크 포트 스캐닝
* 서비스 및 포트 정보 식별
* Docker 기반 취약점 데이터 조회
* MCP(Model Context Protocol) 서버 제공
* Claude Desktop을 활용한 AI 기반 취약점 분석
* 자연어 기반 보안 진단 지원

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
                  │              │
                  │              ▼
                  │      Docker DB Server
                  │
                  ▼
             recon_scan.py
                  │
                  ▼
          분석 결과를 Claude에 전달
                  │
                  ▼
      위험도 분석 및 대응 방안 생성
```

---

## 프로젝트 구조

```text
mini-BAS/
│
├── bas_mcp_server.py             # MCP 서버
├── vulnerability.py              # 취약점 분석 모듈
├── vulnerability_analyzer.py     # Claude 분석 보조 모듈
├── recon_scan.py                 # TCP 포트 스캐너
│
├── db_server/
│   ├── app.py                    # REST API 서버
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── data/
│   │   ├── cves.json
│   │   ├── mappings.json
│   │   └── ports.json
│   └── ...
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 기술 스택

| 분야        | 기술                           |
| --------- | ---------------------------- |
| Language  | Python                       |
| AI        | Claude Desktop               |
| Protocol  | Model Context Protocol (MCP) |
| Database  | JSON 기반 취약점 데이터              |
| Container | Docker                       |
| API       | REST API                     |

---

## 설치 방법

### 1. 저장소 복제

```bash
git clone https://github.com/be-hmn/mini-BAS.git

cd mini-BAS
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

---

## Docker 기반 취약점 데이터베이스 실행

```bash
cd db_server

docker build -t mini-bas-db .

docker run -p 5000:5000 mini-bas-db
```

또는 Docker Compose를 사용하는 경우

```bash
docker compose up
```

---

## MCP 서버 실행

```bash
python bas_mcp_server.py
```

Claude Desktop에서 해당 MCP Server를 등록한 후 사용할 수 있습니다.

---

## 동작 과정

```text
대상 시스템
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
MCP를 통해 Claude Desktop 전달
      │
      ▼
Claude가 결과 분석
      │
      ▼
위험도 및 대응 방안 제공
```

---

## 취약점 데이터 관리

취약점 데이터는 `db_server/data/` 디렉터리에서 JSON 형식으로 관리됩니다.

| 파일              | 설명             |
| --------------- | -------------- |
| `cves.json`     | CVE 및 취약점 정보   |
| `mappings.json` | 서비스와 취약점 매핑 정보 |
| `ports.json`    | 서비스 및 기본 포트 정보 |

필요한 경우 JSON 파일을 수정하여 새로운 취약점이나 서비스를 추가할 수 있습니다.

---

## 활용 예시

* 내부 네트워크 보안 점검
* 취약점 진단 자동화
* MCP 기반 AI Security Agent 개발
* 보안 교육 및 실습
* BAS 연구 프로젝트

---

## 향후 개발 계획

* CVE 데이터 자동 업데이트 기능
* 다양한 스캐닝 기법 지원
* 공격 시나리오 기반 BAS 기능 확장
* 웹 기반 대시보드 개발
* 다양한 LLM 지원

---

## 주의사항

본 프로젝트는 **교육, 연구 및 허가된 환경에서의 보안 진단**을 목적으로 개발되었습니다.

허가받지 않은 시스템을 대상으로 사용하는 것은 법적 책임이 발생할 수 있으며, 사용자는 관련 법률과 규정을 준수해야 합니다.

---

## License

이 프로젝트는 MIT License를 따릅니다.
