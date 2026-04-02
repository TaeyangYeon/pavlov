# DEPLOYMENT.md — Pavlov MVP 배포 가이드

> **🎯 목표**: Intel Mac에서 Docker Compose로 완전 컨테이너화된 MVP 배포

---

## 📋 목차

1. [사전 요구사항](#-사전-요구사항)
2. [첫 배포 (First-time Setup)](#-첫-배포-first-time-setup)
3. [일상 운영](#-일상-운영)
4. [모니터링 및 관리](#-모니터링-및-관리)
5. [백업 및 복구](#-백업-및-복구)
6. [문제 해결](#-문제-해결)
7. [보안 고려사항](#️-보안-고려사항)
8. [성능 최적화](#-성능-최적화)

---

## 🛠 사전 요구사항

### 필수 소프트웨어

| 소프트웨어 | 최소 버전 | 확인 방법 |
|---|---|---|
| **Docker Desktop** | 4.0+ | `docker --version` |
| **Docker Compose** | 2.0+ | `docker-compose --version` |
| **macOS** | macOS 11+ | Intel Mac만 지원 |
| **curl** | 기본 설치됨 | `curl --version` |
| **bc** | 기본 설치됨 | `bc --version` |

### 하드웨어 요구사항

- **CPU**: Intel x86_64 (Apple Silicon M1/M2 지원하지 않음)
- **메모리**: 최소 8GB RAM (16GB 권장)
- **저장공간**: 최소 5GB 여유 공간
- **네트워크**: 인터넷 연결 (Docker 이미지 다운로드용)

### Docker Desktop 설정

```bash
# Docker Desktop이 실행 중인지 확인
docker info

# 필요한 경우 Docker Desktop을 시작하고 다시 확인
open -a Docker
```

---

## 🚀 첫 배포 (First-time Setup)

### 1단계: 환경 변수 설정

```bash
# 1. .env 파일 생성
cp .env.example .env

# 2. 보안 키 생성 (반드시 실행)
echo "Generating SECRET_KEY..."
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

echo "Generating ENCRYPTION_KEY..." 
python3 -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# 3. 강력한 DB 비밀번호 생성
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))"
```

### 2단계: .env 파일 편집

```bash
# 필수 변경 항목들을 .env 파일에 적용
vim .env  # 또는 원하는 에디터 사용
```

**⚠️ 반드시 변경해야 하는 값들:**

```bash
# ── 보안 (1단계에서 생성된 값으로 변경) ──
SECRET_KEY=생성된_32글자_hex_값
ENCRYPTION_KEY=생성된_fernet_키
POSTGRES_PASSWORD=생성된_강력한_비밀번호

# ── AI 서비스 ──
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here

# ── 이메일 알림 (필요시) ──
EMAIL_ENABLED=true
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password  # Gmail App Password
EMAIL_TO=notification_recipient@gmail.com
```

### 3단계: 첫 배포 실행

```bash
# 배포 스크립트 실행
bash scripts/deploy.sh
```

배포 스크립트가 자동으로 수행하는 작업:
- 환경 변수 검증
- Docker 상태 확인
- 포트 충돌 검사
- 서비스 빌드 및 시작
- 헬스 체크 실행

### 4단계: 배포 확인

배포 완료 후 다음 URL에 접근 가능:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

---

## 🔄 일상 운영

### 시작 및 중지

```bash
# 서비스 시작 (백그라운드)
docker-compose up -d

# 서비스 중지
docker-compose down

# 전체 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart backend
```

### 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 로그 확인
docker-compose logs -f        # 모든 서비스
docker-compose logs -f backend # 백엔드만
docker-compose logs -f frontend # 프론트엔드만

# 헬스 체크 실행
bash scripts/health_check.sh
```

### 업데이트 배포

```bash
# 1. 변경사항 확인
git pull origin main

# 2. 서비스 중지
docker-compose down

# 3. 이미지 재빌드
docker-compose build --no-cache

# 4. 서비스 재시작
docker-compose up -d

# 5. 헬스 체크
bash scripts/health_check.sh
```

---

## 📊 모니터링 및 관리

### 헬스 체크

```bash
# 자동 헬스 체크 (스케줄링 가능)
bash scripts/health_check.sh

# API 헬스 체크 (수동)
curl http://localhost:8000/api/v1/health/detailed | jq
```

### 로그 관리

```bash
# 로그 파일 크기 확인
docker system df

# 로그 정리
docker system prune -f

# 특정 컨테이너 로그만 보기
docker-compose logs --tail=100 backend
```

### 리소스 모니터링

```bash
# 컨테이너별 리소스 사용량
docker stats

# 디스크 사용량
docker system df

# 네트워크 상태
docker network ls
docker-compose exec backend netstat -tulpn
```

### PgAdmin (선택사항)

```bash
# PgAdmin 시작
docker-compose --profile admin up -d

# 접속: http://localhost:5050
# 계정: admin@pavlov.local / admin

# PgAdmin 중지
docker-compose --profile admin down
```

---

## 💾 백업 및 복구

### 자동 백업

```bash
# 백업 실행 (자동으로 7개 보관)
bash scripts/backup.sh
```

백업 파일 위치: `./backups/pavlov_backup_YYYYMMDD_HHMMSS.sql.gz`

### 수동 복구

```bash
# 1. 서비스 중지
docker-compose down

# 2. 데이터베이스만 시작
docker-compose up -d postgres

# 3. 백업에서 복구
gunzip -c backups/pavlov_backup_20240326_143022.sql.gz | \
  docker-compose exec -T postgres psql -U pavlov_user -d postgres

# 4. 전체 서비스 재시작
docker-compose up -d

# 5. 복구 확인
bash scripts/health_check.sh
```

### 백업 자동화 (crontab)

```bash
# 매일 새벽 2시 백업
crontab -e

# 다음 라인 추가:
0 2 * * * cd /path/to/pavlov && bash scripts/backup.sh >> logs/backup.log 2>&1
```

---

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 서비스가 시작되지 않음

```bash
# 로그 확인
docker-compose logs

# 포트 충돌 확인
lsof -i :3000
lsof -i :8000

# 컨테이너 상태 확인
docker-compose ps
```

#### 2. 데이터베이스 연결 실패

```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose exec postgres pg_isready -U pavlov_user -d pavlov

# 환경 변수 확인
docker-compose exec backend env | grep DATABASE_URL

# 네트워크 연결 확인
docker-compose exec backend ping postgres
```

#### 3. 프론트엔드가 백엔드에 연결되지 않음

```bash
# nginx 설정 확인
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# 백엔드 접근 테스트
docker-compose exec frontend curl http://backend:8000/api/v1/health
```

#### 4. 메모리 부족

```bash
# 메모리 사용량 확인
docker stats

# 사용하지 않는 이미지/컨테이너 정리
docker system prune -a -f

# Docker Desktop 메모리 할당 늘리기 (GUI 설정)
```

### 응급 복구 절차

```bash
# 1. 모든 서비스 중지
docker-compose down

# 2. 모든 컨테이너 및 이미지 정리
docker system prune -a -f

# 3. 최신 백업에서 복구
bash scripts/backup.sh  # 현재 상태 백업 (가능하면)
# 그 다음 수동 복구 절차 따름

# 4. 처음부터 재배포
bash scripts/deploy.sh
```

---

## 🛡️ 보안 고려사항

### ⚠️ 중요한 보안 설정

#### 1. 환경 변수 보안

```bash
# ✅ 해야 할 것들
- SECRET_KEY와 ENCRYPTION_KEY는 반드시 고유한 값으로 변경
- POSTGRES_PASSWORD는 강력한 비밀번호 사용
- .env 파일은 절대 커밋하지 않음 (이미 .gitignore에 포함됨)
- API 키들은 환경 변수로만 관리

# ❌ 하지 말아야 할 것들
- 기본값 그대로 사용
- .env 파일을 다른 사람과 공유
- 평문으로 비밀번호 저장
- 개발용 키를 운영에서 사용
```

#### 2. 네트워크 보안

```bash
# PostgreSQL은 외부 포트 노출 안 됨 (내부 네트워크만)
# 방화벽 설정 (선택사항)
sudo ufw allow 3000  # Frontend
sudo ufw allow 8000  # Backend API
sudo ufw deny 5432   # PostgreSQL (이미 노출 안 됨)
```

#### 3. 데이터 보호

```bash
# 정기 백업 필수
bash scripts/backup.sh

# 백업 파일 암호화 (민감한 데이터의 경우)
gpg --symmetric backups/pavlov_backup_20240326_143022.sql.gz
```

---

## ⚡ 성능 최적화

### 리소스 최적화

```bash
# Docker Compose 리소스 제한 (docker-compose.yml에 추가 가능)
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
```

### 모니터링 메트릭

```bash
# 애플리케이션 성능 메트릭
curl http://localhost:8000/api/v1/health/detailed

# 주요 확인 항목:
- API 응답 시간 (2초 이하 권장)
- 메모리 사용량 (백엔드 500MB 이하 권장)  
- 데이터베이스 연결 풀 상태
- AI API 호출 비용 알림
```

### 로그 레벨 조정

```bash
# 운영 환경에서는 로그 레벨을 info 또는 warning으로 설정
# .env 파일에서:
LOG_LEVEL=info

# 개발 시에만 debug 사용
LOG_LEVEL=debug
```

---

## 🆘 지원 및 문의

### 로그 수집

문제 발생 시 다음 정보를 수집:

```bash
# 시스템 정보
uname -a
docker --version
docker-compose --version

# 서비스 상태
docker-compose ps
docker-compose logs --tail=50

# 헬스 체크 결과
bash scripts/health_check.sh

# 리소스 사용량
docker stats --no-stream
```

### 개발 모드 실행

개발 및 디버깅을 위한 환경:

```bash
# 개발 모드로 실행 (데이터베이스 포트 노출됨)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 테스트 데이터베이스 포함
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres_test
```

---

## 📝 체크리스트

### 배포 전 체크리스트

- [ ] Docker Desktop 실행 중
- [ ] .env 파일 생성 및 보안 키 설정
- [ ] POSTGRES_PASSWORD 변경됨
- [ ] ANTHROPIC_API_KEY 설정됨 (선택사항)
- [ ] 포트 3000, 8000 사용 가능
- [ ] 최소 5GB 디스크 여유공간 확보

### 배포 후 체크리스트

- [ ] 모든 서비스 실행 중 (`docker-compose ps`)
- [ ] 헬스 체크 통과 (`bash scripts/health_check.sh`)
- [ ] Frontend 접근 가능 (http://localhost:3000)
- [ ] Backend API 접근 가능 (http://localhost:8000/docs)
- [ ] 백업 스크립트 동작 확인 (`bash scripts/backup.sh`)
- [ ] 로그 정상 출력 (`docker-compose logs`)

---

**🎉 배포 완료!** 

Pavlov MVP가 성공적으로 배포되었습니다. 
정기적인 백업과 헬스 체크를 통해 안정적으로 운영하세요.