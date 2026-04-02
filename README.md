# 🦁 pavlov

> **"AI는 적게, 정밀하게. 테스트는 먼저. 감정은 구조로 억제한다."**

감정적 투자 패턴을 구조적으로 억제하고, AI를 의사결정 보조 수단으로만 활용하는  
**포지션 관리 AI 운영 체계**입니다.

---

## 📌 프로젝트 개요

pavlov는 파블로프의 조건반사 실험에서 이름을 따왔습니다.  
이 시스템의 핵심 목적은 감정적 투자 반응(조건반사)을 구조적으로 억제하고, AI 기반으로 의사결정 품질을 높이는 것입니다.

### 핵심 철학

- AI는 의사결정에만 사용한다 (Single AI Call)
- 데이터 수집·계산·필터링은 코드가 담당한다
- 최종 결정 권한은 반드시 사용자에게 있다
- 감정적 매매를 억제하는 구조적 장치를 내장한다

### 시스템 흐름

```
Data → Filter → Indicator → AI (Single Call)
     → Strategy → Cooling-Off Gate → User Decision
```

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
- Python 3.11 (키 생성용)

### 1. 레포지토리 클론

```bash
git clone https://github.com/YOUR_USERNAME/pavlov.git
cd pavlov
mkdir -p backups
```

### 2. 보안 키 생성

```bash
# ENCRYPTION_KEY 생성 (API 키 암호화용)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# SECRET_KEY 생성 (앱 보안용)
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 생성한 키와 Anthropic API 키 입력
```

### 4. 배포

```bash
bash scripts/deploy.sh
```

### 5. 접속

```
http://localhost:3000
```

---

## 🏗️ 아키텍처

```
http://localhost:3000
       │
       ▼
┌─────────────┐
│   nginx     │  (frontend, port 80)
│   React SPA │  → /api/* 프록시
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │  (backend, port 8000)
│ + APScheduler  → KR/US 자동 분석
│ + Recovery  │  → 미실행 복구
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │  (내부 전용, 외부 미노출)
│    15       │  → named volume 영속성
└─────────────┘
```

---

## 🛠️ 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| 스케줄러 | APScheduler 3.x (AsyncIOScheduler) |
| AI | Anthropic Claude (claude-sonnet-4-5) |
| 데이터베이스 | PostgreSQL 15 |
| 시장 데이터 | pykrx (KR), yfinance (US) |
| 암호화 | cryptography (Fernet) |
| 프론트엔드 | React 18, TypeScript, Vite |
| 인프라 | Docker Compose, nginx |
| 개발 방법론 | TDD (pytest), SOLID 원칙 |

---

## ✨ 주요 기능

### 📊 포지션 관리
- 다중 진입가 지원 (가중평균 자동 계산)
- 실현/미실현 손익 실시간 계산 (Decimal 정밀도)
- TP/SL 다단계 판단 (부분 매도 비율 계산)
- 트레일링 스탑 (퍼센트 모드 / ATR 모드)

### 🤖 AI 분석
- 일 1회 Single Call (비용 최적화)
- KR: 16:10 KST (KOSPI 종료 후)
- US: 07:10 KST (NYSE 전일 종가 기준)
- Pydantic 스키마 강제 + 할루시네이션 방어

### 🧠 감정 억제 메커니즘
- **Cooling-Off Gate**: 전략 알림 후 30분 이내 거래 시 경고
- **충동 거래 감지**: 24시간 내 급격한 반전 패턴 감지
- **AI 정렬 점수**: 사용자의 AI 추천 일치율 시각화
- **행동 분석 대시보드**: 과거 거래 패턴 분석

### 🔁 신뢰성
- **Missed Execution Recovery**: 시스템 재시작 시 미실행 분석 자동 복구
- **KR/US 완전 격리**: 한 마켓 실패가 다른 마켓에 영향 없음
- **캐시 프리워밍**: 분석 20분 전 시장 데이터 사전 캐싱

### 📈 백테스트
- 룩어헤드 바이어스 없음 (신호 당일 → 익일 시가 체결)
- 총 수익률, MDD, 승률, 샤프 비율 산출
- ⚠️ 면책 고지 항상 표시

---

## 📡 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/health` | 헬스 체크 |
| GET | `/api/v1/health/detailed` | 컴포넌트별 상태 |
| GET | `/api/v1/positions/` | 포지션 목록 |
| POST | `/api/v1/positions/` | 포지션 생성 |
| GET | `/api/v1/positions/{id}/pnl` | PnL 조회 |
| POST | `/api/v1/positions/{id}/evaluate` | TP/SL 평가 |
| POST | `/api/v1/decisions/` | 거래 결정 기록 |
| GET | `/api/v1/behavior/report` | 행동 분석 리포트 |
| GET | `/api/v1/strategy/latest/{market}` | 최신 전략 조회 |
| POST | `/api/v1/backtest/run` | 백테스트 실행 |
| POST | `/api/v1/scheduler/trigger/{market}` | 수동 분석 실행 |
| GET | `/api/v1/metrics/performance` | 성능 지표 |

> 개발 모드: `http://localhost:8000/docs` (Swagger UI)

---

## 📅 스케줄러

| Job | 일정 | 설명 |
|-----|------|------|
| KR 캐시 프리워밍 | 월~금 15:50 KST | 한국 시장 데이터 사전 캐싱 |
| KR 분석 | 월~금 16:10 KST | KOSPI 종가 기준 AI 분석 |
| US 캐시 프리워밍 | 화~토 06:50 KST | 미국 시장 데이터 사전 캐싱 |
| US 분석 | 화~토 07:10 KST | NYSE 전일 종가 기준 AI 분석 |

---

## 💰 AI 비용 예상

| 항목 | 값 |
|------|-----|
| 모델 | claude-sonnet-4-5 |
| 호출당 예상 비용 | ~$0.012 |
| 월 예상 비용 (44회) | ~$0.53 |
| 비용 경고 임계값 | $0.10 / 호출 |

---

## 🔐 보안

- 모든 시크릿은 환경변수로만 관리 (`.env`)
- API 키 Fernet 암호화 저장 (AES-128-CBC + HMAC)
- 컨테이너 비루트 실행 (`user: pavlov`)
- PostgreSQL 외부 미노출 (내부 네트워크 전용)
- 스택 트레이스 API 응답 미노출

> ⚠️ `.env` 파일은 절대 git에 커밋하지 마세요.  
> ⚠️ `ENCRYPTION_KEY`는 한 번 설정 후 변경 불가 (기존 데이터 복호화 불가)

---

## 🧪 개발 환경

```bash
# 개발 모드 (핫 리로드 + pgAdmin)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 개발 서비스
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000/docs
# pgAdmin:   http://localhost:5050 (admin@pavlov.local / admin)
```

### 테스트 실행

```bash
cd backend

# 단위 테스트
pytest tests/unit/ -v

# 통합 테스트
pytest tests/integration/ -v -m integration

# 전체 커버리지
pytest tests/ --cov=app --cov-report=term-missing -m "not live"
```

### 커버리지 목표

| 모듈 | 목표 | 현재 |
|------|------|------|
| 전체 | ≥ 75% | 90%+ |
| pnl_calculator | 100% | 100% |
| tp_sl_engine | 100% | 100% |
| encryption | 100% | 100% |
| validator | 100% | 100% |

---

## 📂 프로젝트 구조

```
pavlov/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # FastAPI 라우터
│   │   ├── core/             # 설정, DI, 에러 핸들러
│   │   ├── domain/           # 핵심 비즈니스 로직
│   │   │   ├── ai/           # AI 클라이언트, 파이프라인
│   │   │   ├── backtest/     # 백테스트 엔진
│   │   │   ├── behavior/     # 행동 분석, Cooling-Off
│   │   │   ├── filter/       # Rule-Based 필터
│   │   │   ├── indicator/    # RSI, MA, ATR, VolumeRatio
│   │   │   ├── market/       # 마켓 데이터 서비스
│   │   │   ├── notification/ # 알림 서비스
│   │   │   ├── position/     # PnL, TP/SL, Trailing Stop
│   │   │   ├── shared/       # 공통 예외, Result[T]
│   │   │   ├── strategy/     # 전략 통합 엔진
│   │   │   └── user/         # 사용자, API 키 관리
│   │   └── infra/            # DB, 외부 API 어댑터
│   ├── alembic/              # DB 마이그레이션
│   └── tests/                # TDD 테스트
│       ├── unit/
│       └── integration/
├── frontend/
│   ├── src/
│   │   ├── api/              # API 클라이언트
│   │   ├── components/       # React 컴포넌트
│   │   └── hooks/            # 커스텀 훅
│   ├── Dockerfile
│   └── nginx.conf
├── scripts/
│   ├── deploy.sh             # 배포 스크립트
│   ├── health_check.sh       # 헬스 체크
│   └── backup.sh             # DB 백업
├── docker-compose.yml        # 프로덕션
├── docker-compose.dev.yml    # 개발
├── PLAN.md                   # 프로젝트 계획서
├── PROGRESS.md               # 진행사항 기록
├── DEPLOYMENT.md             # 배포 가이드
├── ISOLATION_REPORT.md       # KR/US 격리 검증 리포트
├── PERFORMANCE_REPORT.md     # 성능 최적화 리포트
└── TEST_QUALITY_REPORT.md    # 테스트 품질 리포트
```

---

## 🔧 운영 명령어

```bash
# 시작
docker-compose up -d

# 중지
docker-compose down

# 로그 확인
docker-compose logs -f backend

# DB 백업
bash scripts/backup.sh

# 헬스 체크
bash scripts/health_check.sh

# 수동 분석 실행 (KR)
curl -X POST http://localhost:8000/api/v1/scheduler/trigger/KR

# 성능 지표 확인
curl http://localhost:8000/api/v1/metrics/performance | python3 -m json.tool

# 업데이트
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📋 DB 스키마 (핵심 테이블)

| 테이블 | 목적 |
|--------|------|
| `users` | 사용자 + 암호화된 API 키 |
| `positions` | 포지션 (다중 진입가 JSONB) |
| `market_data` | OHLCV 캐시 (일봉) |
| `analysis_log` | AI 분석 실행 이력 (복구 핵심) |
| `strategy_output` | 생성된 전략 저장 |
| `decision_log` | 사용자 거래 결정 이력 |
| `notifications` | 알림 (인앱 + 이메일) |
| `backtest_results` | 백테스트 결과 |

---

## 🏆 프로젝트 완료 현황

| Phase | Steps | 상태 |
|-------|-------|------|
| Phase 0: 기반 설계 | 1~4 | ✅ |
| Phase 1: 데이터 레이어 | 5~7 | ✅ |
| Phase 2: 필터 및 AI | 8~10 | ✅ |
| Phase 3: 포지션 관리 | 11~15 | ✅ |
| Phase 4: 스케줄러 | 16~17 | ✅ |
| Phase 5: UX 및 안전 장치 | 18~22 | ✅ |
| Phase 6: 검증 및 배포 | 23~27 | ✅ |

**총 27 Steps 완료 · 개발 기간: 2026년 3월 26일 ~ 4월 2일**

---

## 🤝 협업 방식

이 프로젝트는 다음 협업 구조로 개발되었습니다.

| 역할 | 담당 |
|------|------|
| 계획 수립, 프롬프트 작성, 커밋 메시지 | Claude (claude.ai) |
| 실제 코드 구현 | Claude Code |
| Git 커밋/푸시, 최종 의사결정 | 개발자 |

모든 프롬프트는 **PCRO 원칙** (Persona / Context / Restriction / Output Format)을 준수하여 작성되었습니다.

---

## 📄 라이선스

개인 학습 및 투자 보조 목적으로 개발된 프로젝트입니다.

---

<div align="center">

🦁 **pavlov** — 감정은 구조로 억제한다

</div>
# pavlov

> "AI는 적게, 정밀하게. 테스트는 먼저. 감정은 구조로 억제한다."

AI 기반 투자 의사결정 지원 시스템
