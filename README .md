# 🦁 pavlov

> **"AI는 적게, 정밀하게. 테스트는 먼저. 감정은 구조로 억제한다."**

감정적 투자 패턴을 구조적으로 억제하고, AI를 의사결정 보조 수단으로만 활용하는  
**포지션 관리 AI 운영 체계**입니다.

---

## ⚠️ 투자 면책 고지

> pavlov는 **의사결정 지원 도구**이며 자동 매매 시스템이 아닙니다.  
> 모든 최종 투자 결정은 사용자 본인이 내립니다.  
> 과거 성과는 미래 수익을 보장하지 않습니다.

---

## 🚀 빠른 시작

### 사전 요구사항

- Intel Mac (x86_64)
- Docker Desktop 설치 및 실행 중
- Python 3.11 (키 생성 시 필요)

---

### 1단계 — 레포지토리 클론

```bash
git clone https://github.com/YOUR_USERNAME/pavlov.git
cd pavlov
mkdir -p backups
```

---

### 2단계 — 보안 키 생성

```bash
# ENCRYPTION_KEY 생성
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# SECRET_KEY 생성
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

### 3단계 — .env 파일 설정

```bash
cp .env.example .env
open -a TextEdit .env
```

아래 항목을 반드시 실제 값으로 교체하세요.

```env
# 위에서 생성한 키로 교체 (플레이스홀더 그대로 두면 실행 안 됨)
SECRET_KEY=실제_생성한_키_입력
ENCRYPTION_KEY=실제_생성한_키_입력

# DB 비밀번호 (원하는 값으로 설정)
POSTGRES_PASSWORD=원하는_비밀번호

# Anthropic API 키 (나중에 입력해도 됨)
ANTHROPIC_API_KEY=sk-ant-api03-...

# ⚠️ 반드시 확인: 이 줄 끝에 % 가 없어야 합니다
SLOW_QUERY_THRESHOLD_MS=100
```

> ⚠️ **주의**: `SLOW_QUERY_THRESHOLD_MS=100%` 처럼 `%`가 붙으면  
> 그 아래 줄이 모두 무시되어 DB 연결 실패가 발생합니다.

---

### 4단계 — 실행

```bash
docker-compose up -d
```

처음 실행 시 이미지 빌드로 3~5분 소요됩니다.

---

### 5단계 — 확인

```bash
# 30초 후 상태 확인
sleep 30 && docker-compose ps
```

정상 상태:
```
NAME              STATUS
pavlov_postgres   Up (healthy)
pavlov_backend    Up (healthy)
pavlov_frontend   Up (healthy)
```

```bash
# 헬스 체크
curl http://localhost:8000/api/v1/health
# {"status":"ok","version":"0.1.0","environment":"production"}
```

---

### 6단계 — 브라우저 접속

```
http://localhost:3000
```

> ⚠️ **반드시 포트 3000으로 접속하세요.**  
> `http://localhost` (포트 없음)로 접속하면 API 연결 오류가 발생합니다.

---

## 🔑 Anthropic API 키 설정

AI 분석 기능을 사용하려면 API 키가 필요합니다.  
키 없이도 포지션 관리, PnL 계산, 백테스트는 정상 작동합니다.

**API 키 발급**: https://console.anthropic.com → API Keys → Create Key

### 방법 A — .env 파일 수정 (권장)

```bash
open -a TextEdit ~/pavlov/.env
```

이 줄을 찾아서:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

실제 키로 교체 후 저장:
```
ANTHROPIC_API_KEY=sk-ant-api03-여기에실제키
```

저장 후 재시작:
```bash
cd ~/pavlov && docker-compose restart backend
```

### 방법 B — UI에서 입력

1. `http://localhost:3000` 접속
2. 왼쪽 사이드바 **⚙️ 설정** 클릭
3. API 키 입력창에 키 붙여넣기
4. **저장 & 검증** 클릭
5. ✅ 표시되면 완료

---

## 📋 첫 사용 순서

1. `http://localhost:3000` 접속
2. **💼 포지션** → `+ 새 포지션` → 종목/진입가/수량 입력
3. **📅 스케줄러** → **KR 분석 실행** 또는 **US 분석 실행** 클릭
4. **🤖 AI 전략** 탭에서 분석 결과 확인
5. **📊 대시보드**에서 전체 현황 확인

---

## 🏗️ 아키텍처

```
http://localhost:3000
       │
       ▼
┌─────────────┐
│   nginx     │  (frontend, port 3000 → 내부 80)
│   React SPA │  /api/* → backend:8000 프록시
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │  (backend, port 8000)
│ + APScheduler  → KR/US 자동 분석
│ + Alembic   │  → 시작 시 자동 마이그레이션
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │  (내부 전용, 외부 미노출)
│    15       │  named volume 영속성
└─────────────┘
```

---

## 🛠️ 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| 스케줄러 | APScheduler 3.x |
| AI | Anthropic Claude (claude-sonnet-4-5) |
| 데이터베이스 | PostgreSQL 15 |
| 시장 데이터 | pykrx (KR), yfinance (US) |
| 암호화 | cryptography (Fernet AES-128) |
| 프론트엔드 | React 18, TypeScript, Vite, nginx |
| 인프라 | Docker Compose, Intel Mac x86_64 최적화 |
| Node.js | 20-alpine (Vite 요구사항) |

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 포지션 관리 | 다중 진입가, 가중평균 자동 계산 |
| PnL 계산 | 실현/미실현 손익 (Decimal 정밀도) |
| TP/SL 엔진 | 다단계 부분 매도 판단 |
| 트레일링 스탑 | 퍼센트/ATR 모드 |
| AI 분석 | 1일 1회 Single Call (비용 최적화) |
| 자동 스케줄 | KR 16:10 KST / US 07:10 KST |
| 복구 로직 | 미실행 분석 자동 복구 |
| 감정 억제 | Cooling-Off, 행동 분석, AI 정렬 점수 |
| 백테스트 | 과거 데이터 전략 시뮬레이션 |
| 알림 | 전략 변경, TP/SL 트리거, 충동 경고 |

---

## 📅 자동 스케줄

| Job | 시간 | 설명 |
|-----|------|------|
| KR 캐시 준비 | 월~금 15:50 KST | 한국 시장 데이터 사전 로딩 |
| KR 분석 | 월~금 16:10 KST | KOSPI 종가 기준 AI 분석 |
| US 캐시 준비 | 화~토 06:50 KST | 미국 시장 데이터 사전 로딩 |
| US 분석 | 화~토 07:10 KST | NYSE 전일 종가 기준 AI 분석 |

---

## 💰 AI 비용

| 항목 | 값 |
|------|-----|
| 모델 | claude-sonnet-4-5 |
| 호출당 예상 비용 | ~$0.012 |
| 월 예상 비용 | ~$0.53 (44회/월) |

---

## 🔧 매일 사용 명령어

```bash
# 시작
cd ~/pavlov && docker-compose up -d

# 종료
cd ~/pavlov && docker-compose down

# 로그 확인
docker-compose logs -f backend

# 상태 확인
docker-compose ps

# DB 백업
bash scripts/backup.sh

# 헬스 체크
bash scripts/health_check.sh
```

---

## 🐛 자주 발생하는 문제 및 해결법

### ❌ 백엔드가 계속 재시작됨

```bash
docker-compose logs backend --tail=30
```

| 에러 메시지 | 원인 | 해결 |
|------------|------|------|
| `Field required: POSTGRES_USER` | `.env`에서 `%` 때문에 파싱 중단 | `SLOW_QUERY_THRESHOLD_MS=100%` → `100`으로 수정 |
| `ValidationError: SECRET_KEY` | 플레이스홀더 값 그대로 | 실제 생성한 키로 교체 |
| `DuplicateObjectError: type already exists` | DB 볼륨 재사용 충돌 | `docker-compose down -v && docker-compose up -d` |

---

### ❌ API 연결 오류 (ERR_CONNECTION_REFUSED)

브라우저 콘솔에 이런 오류가 나올 때:
```
GET http://localhost/api/v1/positions/ net::ERR_CONNECTION_REFUSED
```

**원인**: 포트 없이 `http://localhost`(포트 80)로 접속했기 때문입니다.

**해결**: 반드시 포트 3000으로 접속하세요.
```
http://localhost:3000   ← ✅ 정상
http://localhost        ← ❌ 오류 발생
```

---

### ❌ 프론트엔드 빌드 실패

```
Vite requires Node.js version 20.19+
```

**해결**: `frontend/Dockerfile` 첫 줄 확인
```dockerfile
FROM node:20-alpine AS builder   ← ✅ 20 이상
FROM node:18-alpine AS builder   ← ❌ 18은 안 됨
```

---

### ❌ nginx 시작 실패

```
invalid value "must-revalidate" in nginx.conf
```

**해결**: `frontend/nginx.conf`에서 `gzip_proxied` 줄 수정
```nginx
# ❌ 잘못된 설정
gzip_proxied expired no-cache no-store private must-revalidate auth;

# ✅ 올바른 설정
gzip_proxied expired no-cache no-store private auth;
```

---

### ❌ DB 마이그레이션 반복 실패

```bash
# 볼륨 포함 완전 초기화
docker-compose down -v
docker-compose up -d
```

---

## 🔐 보안 주의사항

- `.env` 파일은 절대 git에 커밋하지 마세요 (`.gitignore`에 포함됨)
- `ENCRYPTION_KEY`는 설정 후 변경 불가 (기존 암호화 데이터 복호화 불가)
- `SECRET_KEY`와 `ENCRYPTION_KEY`는 개발/운영 환경에서 각각 다른 값 사용
- `POSTGRES_PASSWORD`는 강력한 비밀번호로 설정

---

## 📂 프로젝트 구조

```
pavlov/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # FastAPI 라우터
│   │   ├── core/             # 설정, DI, 에러 핸들러
│   │   ├── domain/           # 비즈니스 로직
│   │   └── infra/            # DB, 외부 API 어댑터
│   ├── alembic/              # DB 마이그레이션
│   ├── Dockerfile            # python:3.11-slim 멀티스테이지
│   └── tests/                # 테스트 (커버리지 90%+)
├── frontend/
│   ├── src/
│   │   ├── api/              # API 클라이언트 (상대경로)
│   │   ├── components/       # React 컴포넌트
│   │   └── hooks/            # 커스텀 훅
│   ├── Dockerfile            # node:20-alpine 빌드
│   └── nginx.conf            # /api/* 프록시 설정
├── scripts/
│   ├── deploy.sh             # 배포 자동화
│   ├── health_check.sh       # 배포 후 검증
│   └── backup.sh             # DB 백업 (7일 보관)
├── docker-compose.yml        # 프로덕션 설정
├── docker-compose.dev.yml    # 개발 오버라이드
└── .env.example              # 환경변수 템플릿
```

---

## 🏆 개발 현황

| Phase | Steps | 내용 | 상태 |
|-------|-------|------|------|
| 0: 기반 설계 | 1~4 | 환경, AI 계약, DB, 아키텍처 | ✅ |
| 1: 데이터 레이어 | 5~7 | 마켓 어댑터, 캐싱, 지표 | ✅ |
| 2: 필터 및 AI | 8~10 | 필터, AI 클라이언트, 파이프라인 | ✅ |
| 3: 포지션 관리 | 11~15 | 입력, PnL, TP/SL, 트레일링, 통합 | ✅ |
| 4: 스케줄러 | 16~17 | 스케줄러, 복구 로직 | ✅ |
| 5: UX 및 안전 | 18~22 | 알림, 암호화, UI, 격리, 감정억제 | ✅ |
| 6: 검증 및 배포 | 23~27 | 에러, 테스트, 백테스트, 최적화, 배포 | ✅ |

**총 27 Steps 완료 · 테스트 커버리지 90%+**

---

<div align="center">

🦁 **pavlov** — 감정은 구조로 억제한다

</div>
