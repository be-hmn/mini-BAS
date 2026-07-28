# mini-BAS

## 프로젝트 소개

**mini-BAS**는 Python 기반의 **BAS(Breach and Attack Simulation)** 프레임워크입니다.

대상 시스템의 네트워크를 스캔하고, 발견된 서비스를 기반으로 알려진 취약점을 분석하여 공격 가능성을 평가하는 경량 BAS 시스템입니다.

또한 **MCP(Model Context Protocol)**를 통해 AI Agent가 보안 진단 기능을 호출할 수 있도록 설계되었으며, Docker 기반 취약점 데이터베이스와 연동하여 자동화된 보안 평가를 수행합니다.

---

## 주요 기능

* 멀티스레드 TCP 포트 스캐닝
* 취약점 데이터베이스 기반 취약점 분석
* MCP 기반 보안 진단 도구 제공
* Docker 기반 취약점 DB 연동
* Claude API를 활용한 AI 기반 취약점 분석
* CVE 모듈을 손쉽게 추가할 수 있는 확장형 구조

---

## 시스템 구조

```text
                MCP Client / AI Agent
                        │
                        │
               bas_mcp_server.py
                        │
                vulnerability.py
                 /              \
                /                \
     recon_scan.py      Docker 기반 취약점 DB
                \
                 \
        vulnerability_analyzer.py
           (Claude API 분석)
```

---

## 프로젝트 구조

```text
mini-BAS/
│
├── bas_mcp_server.py             # MCP 서버
├── vulnerability.py              # 취약점 분석 모듈
├── vulnerability_analyzer.py     # AI 기반 취약점 분석
├── recon_scan.py                 # TCP 포트 스캐너
│
├── killchains/                   # CVE별 Kill Chain 정의
│
├── db_server/                    # Docker 기반 취약점 DB
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── ...
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 실행 환경

* Python 3.11 이상
* Docker
* pip

---

## 설치

저장소를 내려받습니다.

```bash
git clone https://github.com/be-hmn/mini-BAS.git

cd mini-BAS
```

필요한 라이브러리를 설치합니다.

```bash
pip install -r requirements.txt
```

---

## 환경 변수

`.env` 파일을 생성합니다.

```env
ANTHROPIC_API_KEY=YOUR_API_KEY
DB_URL=http://localhost:5000
```

---

## Docker 기반 취약점 DB 실행

```bash
cd db_server

docker build -t mini-bas-db .

docker run -p 5000:5000 mini-bas-db
```

또는

```bash
docker compose up
```

---

## MCP 서버 실행

```bash
python bas_mcp_server.py
```

---

## 동작 과정

```text
대상 시스템
      │
      ▼
포트 스캔
      │
      ▼
열린 포트 식별
      │
      ▼
취약점 데이터베이스 조회
      │
      ▼
위험도 분석
      │
      ▼
공격 가능 경로 제안
```

---

## 새로운 CVE 모듈 추가

새로운 CVE를 추가하려면 다음 순서를 따르면 됩니다.

1. 새로운 Python 파일 생성

```
<cve>.py
```

2. 아래 인터페이스 구현

```python
scan(target, exploit_result=None)

exploit(target)
```

3. `killchains/` 폴더에 JSON 정의 추가

```
killchains/<cve>.json
```

MCP 서버는 실행 시 해당 모듈을 자동으로 인식하여 새로운 도구를 등록합니다.

---

## 사용 기술

* Python
* MCP (Model Context Protocol)
* Docker
* SQLite
* REST API
* Anthropic Claude API

---

## 향후 개발 계획

* 다양한 CVE 모듈 추가
* 공격 시뮬레이션 기능 고도화
* 취약점 분석 정확도 향상
* 웹 기반 대시보드 개발
* AI 기반 자동 공격 경로 추천 기능 개선

---

## 주의사항

본 프로젝트는 **교육 및 연구 목적**으로 개발되었습니다.

허가받지 않은 시스템에 대한 공격이나 침투 테스트에 사용해서는 안 되며, 반드시 적법한 환경에서만 사용해야 합니다.
