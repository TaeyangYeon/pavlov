# PLAN.md — pavlov 프로젝트 계획서

> **"AI는 적게, 정밀하게. 테스트는 먼저. 감정은 구조로 억제한다."**

---

## 1. 프로젝트 비전

이 시스템은 단순한 도구가 아닙니다.
감정적 투자 패턴을 구조적으로 억제하고, AI를 의사결정 보조 수단으로만 활용하는
**포지션 관리 AI 운영 체계**입니다.

### 핵심 철학

- AI는 의사결정에만 사용한다
- 데이터 수집·계산·필터링은 코드가 담당한다
- 최종 결정 권한은 반드시 사용자에게 있다
- 감정적 매매를 억제하는 구조적 장치를 내장한다

### 시스템 철학 흐름

```
Data → Filter → Indicator → AI(Single Call) → Strategy → Cooling-Off → User Decision
```

---

## 2. 설계 결정 맥락

### 2-1. 언어 스택

| 구성 요소 | 선택 | 이유 |
|---|---|---|
| 백엔드 | Python 3.11 + FastAPI | 금융 라이브러리 생태계, AI SDK 퍼스트, TDD 적합 |
| ORM | SQLAlchemy + Alembic | 비동기 지원, 마이그레이션 관리 |
| 테스트 | pytest + pytest-cov | TDD 사이클 최적화 |
| 린터 | ruff + black | 빠른 피드백 루프 |
| 타입 체크 | mypy | SOLID 인터페이스 검증 |
| 프론트엔드 | React + TypeScript | 타입 안전성 |

### 2-2. 개발 환경 (Intel Mac 최적화)

| 구성 요소 | 선택 | 이유 |
|---|---|---|
| 패키지 관리 | pyenv + venv | 시스템 Python 오염 방지 |
| 컨테이너 | Docker Desktop (Intel x86_64) | 환경 재현성, ARM 패키지 혼입 방지 |
| DB (로컬) | PostgreSQL 15 via Docker | ARM 이미지 불필요 |
| CI | GitHub Actions | push 시 자동 테스트 |

> ⚠️ GPU 의존 라이브러리(tensorflow-metal 등) 사용 금지. AI는 외부 API 호출로만 사용.

### 2-3. TDD 적용 범위

| 모듈 | 테스트 유형 | 우선순위 |
|---|---|---|
| PnL 계산 엔진 | 단위 테스트 (결정론적) | 🔴 최우선 |
| TP/SL 판단 로직 | 단위 테스트 (결정론적) | 🔴 최우선 |
| Rule-Based 필터 | 단위 테스트 | 🟠 높음 |
| AI 응답 파서 | 단위 테스트 (mock) | 🟠 높음 |
| 스케줄러/복구 | 통합 테스트 | 🟡 중간 |
| API 엔드포인트 | 통합 테스트 | 🟡 중간 |
| 알림 시스템 | E2E 테스트 | 🟢 낮음 |

### 2-4. SOLID 원칙 적용

| 원칙 | 적용 위치 | 구체적 방법 |
|---|---|---|
| S (단일 책임) | 모든 서비스 클래스 | DataFetcher / IndicatorEngine / AIClient 분리 |
| O (개방-폐쇄) | 필터/지표 엔진 | 새 필터 추가 시 기존 코드 수정 없이 클래스 추가 |
| L (리스코프 치환) | 마켓 어댑터 (KR/US) | 동일 인터페이스로 완전 치환 가능 |
| I (인터페이스 분리) | FastAPI Pydantic 모델 | 요청/응답마다 별도 스키마 |
| D (의존성 역전) | AI 클라이언트, DB 레이어 | 추상 인터페이스에 의존, 테스트 시 mock 교체 |

---

## 3. 시스템 아키텍처

### 전체 구조

```
[사용자 입력 + AI API 키]
        ↓
[FastAPI Backend (Python)]
        ↓
[Data Layer] ─── pykrx(KR) / yfinance(US)
        ↓
[Rule-Based Filter Engine]
        ↓
[Indicator Engine] ─── RSI / MA / ATR / Volume
        ↓
[AI Prompt Builder] ─── Single Call
        ↓
[AI Client (사용자 API Key)]
        ↓
[Strategy Parser + Validator]
        ↓
[Position Management Engine]
        ↓
[Cooling-Off Gate] ─── 감정 억제 장치
        ↓
[Notification + UI Dashboard]
```

### 마켓 분리 구조

| 항목 | 한국 시장 (KR) | 미국 시장 (US) |
|---|---|---|
| 데이터 소스 | pykrx | yfinance |
| 실행 시점 | 16:10 KST | 07:10 KST |
| 어댑터 클래스 | KRMarketAdapter | USMarketAdapter |
| 통화 | KRW | USD |

### 디렉토리 구조

```
pavlov/
├── PLAN.md                   ← 이 파일 (프로젝트 계획서)
├── PROGRESS.md               ← 진행사항 기록
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI 라우터
│   │   ├── core/             # 설정, 의존성 주입
│   │   ├── domain/           # 핵심 비즈니스 로직
│   │   │   ├── market/       # MarketAdapter 인터페이스 + KR/US 구현
│   │   │   ├── position/     # 포지션 관리 엔진
│   │   │   ├── filter/       # Rule-Based 필터 엔진
│   │   │   ├── indicator/    # 지표 엔진
│   │   │   ├── ai/           # AI 클라이언트 + 프롬프트 빌더
│   │   │   └── strategy/     # 전략 파서 + 검증
│   │   └── infra/            # DB, 외부 API 어댑터
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       └── integration/
├── frontend/                 # React + TypeScript
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## 4. 데이터베이스 설계

| 테이블명 | 목적 |
|---|---|
| users | 사용자 및 암호화된 AI API 키 관리 |
| positions | 포지션 추적 (다중 진입가 지원) |
| market_data | 일봉 OHLC 캐싱 (API 중복 호출 방지) |
| analysis_log | 실행 여부 추적 (복구 로직 핵심) |
| strategy_output | 생성된 전략 저장 |
| decision_log | 사용자 결정 이력 (감정 패턴 분석용) |

> 💡 `decision_log`: AI 전략을 따랐는지 무시했는지 기록 → 감정적 패턴 시각화에 활용

---

## 5. AI 프롬프트 설계 (선행 정의)

### 입력 구조 (Prompt Input)

```json
{
  "market": "KR | US",
  "date": "YYYY-MM-DD",
  "filtered_stocks": [
    {
      "ticker": "005930",
      "name": "삼성전자",
      "close": 71500,
      "volume_ratio": 1.8,
      "rsi_14": 42.3,
      "ma_20": 70200,
      "ma_60": 68900,
      "atr_14": 1200
    }
  ],
  "held_positions": [
    {
      "ticker": "005930",
      "avg_price": 69000,
      "quantity": 10,
      "current_pnl_pct": 3.6
    }
  ]
}
```

### 출력 구조 (Prompt Output)

```json
{
  "market_summary": "string (한국어 200자 이내)",
  "strategies": [
    {
      "ticker": "005930",
      "action": "hold | buy | partial_sell | full_exit",
      "take_profit": [{"pct": 10, "sell_ratio": 0.3}],
      "stop_loss": [{"pct": -5, "sell_ratio": 0.5}],
      "rationale": "string (100자 이내)",
      "confidence": 0.0
    }
  ]
}
```

---

## 6. 개발 단계 계획

### Phase 0: 기반 설계

| Step | 내용 | 상태 |
|---|---|---|
| Step 1 | 개발 환경 세팅 (Intel Mac 최적화) | ⬜ |
| Step 2 | AI 프롬프트 설계 및 계약 정의 | ⬜ |
| Step 3 | DB 스키마 설계 및 마이그레이션 | ⬜ |
| Step 4 | 아키텍처 골격 및 의존성 주입 | ⬜ |

### Phase 1: 데이터 레이어

| Step | 내용 | 상태 |
|---|---|---|
| Step 5 | 마켓 데이터 어댑터 (KR/US) | ⬜ |
| Step 6 | 시장 데이터 저장 및 캐싱 | ⬜ |
| Step 7 | 지표 엔진 (RSI / MA / ATR) | ⬜ |

### Phase 2: 필터 및 AI

| Step | 내용 | 상태 |
|---|---|---|
| Step 8 | Rule-Based 필터 엔진 | ⬜ |
| Step 9 | AI 클라이언트 및 프롬프트 빌더 | ⬜ |
| Step 10 | AI 응답 파서 및 검증 | ⬜ |

### Phase 3: 포지션 관리

| Step | 내용 | 상태 |
|---|---|---|
| Step 11 | 포지션 입력 API + 최소 UI | ⬜ |
| Step 12 | PnL 계산 엔진 | ⬜ |
| Step 13 | TP/SL 판단 엔진 | ⬜ |
| Step 14 | 트레일링 스탑 엔진 | ⬜ |
| Step 15 | 전략 통합 엔진 | ⬜ |

### Phase 4: 스케줄러 및 신뢰성

| Step | 내용 | 상태 |
|---|---|---|
| Step 16 | 스케줄러 설정 (KR/US) | ⬜ |
| Step 17 | Missed Execution 복구 로직 | ⬜ |

### Phase 5: 사용자 경험 및 안전 장치

| Step | 내용 | 상태 |
|---|---|---|
| Step 18 | 알림 시스템 | ⬜ |
| Step 19 | API 키 관리 (암호화) | ⬜ |
| Step 20 | UI 대시보드 완성 | ⬜ |
| Step 21 | KR/US 마켓 완전 분리 검증 | ⬜ |
| Step 22 | 감정 억제 메커니즘 (Cooling-Off) | ⬜ |

### Phase 6: 검증 및 배포

| Step | 내용 | 상태 |
|---|---|---|
| Step 23 | 에러 처리 강화 | ⬜ |
| Step 24 | 단위/통합 테스트 전수 검증 | ⬜ |
| Step 25 | 백테스트 모듈 | ⬜ |
| Step 26 | 성능 최적화 | ⬜ |
| Step 27 | MVP 배포 | ⬜ |

---

## 7. 리스크 및 대응

| 리스크 | 대응 전략 | 우선순위 |
|---|---|---|
| AI 할루시네이션 | JSON 스키마 강제 + Pydantic 이중 검증 | 🔴 최우선 |
| API 비용 폭발 | Single Call 원칙 + 일 1회 실행 | 🔴 최우선 |
| Intel Mac 호환성 | Docker 격리 + GPU 라이브러리 배제 | 🟠 높음 |
| 사용자 감정적 무시 | Cooling-Off + Decision Log 시각화 | 🟠 높음 |
| 데이터 소스 장애 | KR/US 독립 실행 + 폴백 처리 | 🟡 중간 |
| 법적 리스크 | 의사결정 지원 도구 명시 + 면책 고지 | 🟡 중간 |

---

## 8. 협업 규칙

- **Claude (claude.ai)**: 계획 수립, 프롬프트 작성, 커밋 메시지 작성
- **Claude Code**: 실제 코드 구현
- **개발자**: Git 커밋/푸시, 최종 의사결정
- **프롬프트 규칙**: PCRO 원칙 준수 (Persona / Context / Restriction / Output)

---

*최종 수정: Step 1 완료 후*
