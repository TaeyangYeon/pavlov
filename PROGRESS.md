# PROGRESS.md — pavlov 진행사항

> 새로운 채팅방에서 이어갈 때: PLAN.md + PROGRESS.md 두 파일을 함께 업로드하세요.

---

## 진행 현황 요약

| Phase | 내용 | 진행률 |
|---|---|---|
| Phase 0: 기반 설계 | Step 1~4 | 1/4 |
| Phase 1: 데이터 레이어 | Step 5~7 | 0/3 |
| Phase 2: 필터 및 AI | Step 8~10 | 0/3 |
| Phase 3: 포지션 관리 | Step 11~15 | 0/5 |
| Phase 4: 스케줄러 | Step 16~17 | 0/2 |
| Phase 5: UX 및 안전 장치 | Step 18~22 | 0/5 |
| Phase 6: 검증 및 배포 | Step 23~27 | 0/5 |

**전체 진행률: 1 / 27 Steps**

---

## Step별 상세 기록

---

### ✅ Step 1 — 개발 환경 세팅 (완료)

**날짜**: 2026-03-26
**소요 시간**: 약 30분
**담당**: Claude Code

#### 완료된 작업

- [x] Python 3.11.15 확인 (pyenv)
- [x] Docker Desktop 27.4.0 확인 및 실행
- [x] pyenv 2.6.25 확인
- [x] 전체 디렉토리 구조 생성 (DDD 원칙 적용)
- [x] pyproject.toml 생성 (runtime + dev 의존성 분리)
- [x] docker-compose.yml 생성 (PostgreSQL 15, dev + test DB)
- [x] .env.example 생성
- [x] backend/app/main.py (FastAPI + health endpoint)
- [x] backend/app/core/config.py (pydantic-settings)
- [x] backend/app/infra/db/base.py (AsyncSQLAlchemy)
- [x] backend/tests/conftest.py (pytest async fixtures)
- [x] .github/workflows/ci.yml (lint + typecheck + test)
- [x] setup-test-env.sh, run-tests.sh 헬퍼 스크립트

#### 테스트 결과

```
4 passed, 1 failed
- ✅ Unit tests: PASSING (test_config.py, test_main.py)
- ⚠️ Integration test: DB connectivity (미해결 — Step 3 Alembic 설정 후 해결 예정)
- ✅ Linting: ruff PASS
- ✅ Formatting: black PASS
```

#### 커밋 메시지

```
feat: initialize pavlov project development environment (Step 1)
```

#### 미해결 이슈

- [ ] DB 연결 통합 테스트 1개 실패 → Step 3 (Alembic 마이그레이션) 완료 후 해결

#### 다음 Step 준비사항

- Step 2: AI 프롬프트 설계 및 계약 정의
  - Pydantic 입출력 스키마 작성
  - 프롬프트 템플릿 초안 작성

---

### ⬜ Step 2 — AI 프롬프트 설계 및 계약 정의

**상태**: 대기 중

---

### ⬜ Step 3 — DB 스키마 설계 및 마이그레이션

**상태**: 대기 중

---

### ⬜ Step 4 — 아키텍처 골격 및 의존성 주입

**상태**: 대기 중

---

### ⬜ Step 5 — 마켓 데이터 어댑터 (KR/US)

**상태**: 대기 중

---

### ⬜ Step 6 — 시장 데이터 저장 및 캐싱

**상태**: 대기 중

---

### ⬜ Step 7 — 지표 엔진 (RSI / MA / ATR)

**상태**: 대기 중

---

### ⬜ Step 8 — Rule-Based 필터 엔진

**상태**: 대기 중

---

### ⬜ Step 9 — AI 클라이언트 및 프롬프트 빌더

**상태**: 대기 중

---

### ⬜ Step 10 — AI 응답 파서 및 검증

**상태**: 대기 중

---

### ⬜ Step 11 — 포지션 입력 API + 최소 UI

**상태**: 대기 중

---

### ⬜ Step 12 — PnL 계산 엔진

**상태**: 대기 중

---

### ⬜ Step 13 — TP/SL 판단 엔진

**상태**: 대기 중

---

### ⬜ Step 14 — 트레일링 스탑 엔진

**상태**: 대기 중

---

### ⬜ Step 15 — 전략 통합 엔진

**상태**: 대기 중

---

### ⬜ Step 16 — 스케줄러 설정 (KR/US)

**상태**: 대기 중

---

### ⬜ Step 17 — Missed Execution 복구 로직

**상태**: 대기 중

---

### ⬜ Step 18 — 알림 시스템

**상태**: 대기 중

---

### ⬜ Step 19 — API 키 관리 (암호화)

**상태**: 대기 중

---

### ⬜ Step 20 — UI 대시보드 완성

**상태**: 대기 중

---

### ⬜ Step 21 — KR/US 마켓 완전 분리 검증

**상태**: 대기 중

---

### ⬜ Step 22 — 감정 억제 메커니즘 (Cooling-Off)

**상태**: 대기 중

---

### ⬜ Step 23 — 에러 처리 강화

**상태**: 대기 중

---

### ⬜ Step 24 — 단위/통합 테스트 전수 검증

**상태**: 대기 중

---

### ⬜ Step 25 — 백테스트 모듈

**상태**: 대기 중

---

### ⬜ Step 26 — 성능 최적화

**상태**: 대기 중

---

### ⬜ Step 27 — MVP 배포

**상태**: 대기 중

---

## 새 채팅방 인수인계 템플릿

> 새 채팅방 시작 시 아래 내용을 첫 메시지로 붙여넣으세요.

```
PLAN.md와 PROGRESS.md를 업로드합니다.

현재 상황:
- 마지막 완료 Step: Step 1 (개발 환경 세팅)
- 다음 진행할 Step: Step 2 (AI 프롬프트 설계)
- 미해결 이슈: DB 통합 테스트 1개 실패 (Step 3에서 해결 예정)

규칙:
- Claude (claude.ai): 계획 수립, PCRO 프롬프트 작성, 커밋 메시지 작성
- Claude Code: 실제 코드 구현
- 개발자: Git 커밋/푸시
- 다음 Step의 Claude Code 프롬프트를 PCRO 규칙으로 작성해줘.
```
