# 📚 Baseball & Tetris Game API

## 🏫 1. 프로젝트 소개
**Baseball & Tetris Game API**는 숫자 야구 게임과 테트리스 게임을 위한 RESTful API 서비스로, **동시성 제어**와 **안정적인 인증 시스템**을 통해 효율적인 게임 서비스를 제공합니다.
 
- **배포 상황**: 🚀 *AWS EC2를 통해 배포 중*

## ✅ 2. 프로젝트 핵심 목표
- **🎮 게임 시스템**: 안정적인 **숫자 야구** 및 **테트리스** 게임 API 구축  
- **🔒 보안 강화**: JWT 기반 **인증 시스템** 및 **소셜 로그인(카카오)** 구현  
- **⚡ 동시성 제어**: 게임 진행 중 발생할 수 있는 **데이터 정합성** 보장  
- **🔔 사용자 경험**: 유저 편의를 위한 **게임 기록 관리** 기능 구현  
- **🔧 CI/CD 구축**: GitHub Actions 및 Docker를 활용한 **자동화 배포**

## 📌 3. KEY SUMMARY
### 🔷 주요 기능

<details>
<summary><b>🔹 숫자 야구 게임</b></summary>

### 게임 규칙
- 랜덤으로 생성된 숫자(중복 없음)를 맞추는 게임
- 자릿수와 숫자가 모두 일치하면 스트라이크
- 숫자만 일치하고 자릿수가 다르면 볼
- 최대 시도 횟수는 10회

### 주요 기능
- 새 게임 생성 (3자리 이상 숫자)
- 숫자 추측 및 결과 확인
- 게임 상태 조회
- 게임 포기 기능
- 로그인한 사용자의 게임 기록 저장
</details>

<details>
<summary><b>🔹 테트리스 게임</b></summary>

### 게임 규칙
- 클래식 테트리스 게임 룰 적용
- 블록을 회전, 이동하여 완성된 라인 제거
- 레벨에 따른 난이도 증가

### 주요 기능
- 게임 생성 및 상태 관리
- 블록 이동, 회전, 드롭 기능
- 블록 홀드 기능
- 게임 일시정지/재개
- 점수 시스템 및 리더보드
- 로그인한 사용자의 최고 점수 기록
</details>

<details>
<summary><b>🔹 사용자 인증</b></summary>

### 인증 시스템
- JWT 기반 토큰 인증
- 액세스 토큰 및 리프레시 토큰 관리
- 토큰 자동 갱신 미들웨어
- 보안 강화된 비밀번호 관리

### 소셜 로그인
- 카카오 OAuth 연동
- 토큰 기반 인증 관리
- 소셜 계정과 기존 계정 연동
</details>

### 🔧 기술적 성과
-  **JWT** 기반 안정적인 인증 시스템 구현
-  **GitHub Actions**를 활용한 자동화된 배포 환경 구축
-  **Docker**를 통한 일관된 개발/배포 환경 구성
-  **카카오 소셜 로그인** 연동 구현
-  **동시성 제어**를 통한 데이터 정합성 보장

## 🏗️ 4. 적용 기술
### Backend
- ![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)  
- ![FastAPI](https://img.shields.io/badge/FastAPI-0.115.8-009688?logo=fastapi&logoColor=white)  
- ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.38-red?logo=sqlalchemy&logoColor=white)  
- ![JWT](https://img.shields.io/badge/JWT-Security-000000?logo=jsonwebtokens&logoColor=white)  
- ![Pydantic](https://img.shields.io/badge/Pydantic-2.10.6-E92063?logo=pydantic&logoColor=white)

### Database
- ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)  

### DevOps
- ![AWS](https://img.shields.io/badge/AWS-EC2-232F3E?logo=amazonaws&logoColor=white)  
- ![Docker](https://img.shields.io/badge/Docker-Containerization-2496ED?logo=docker&logoColor=white)  
- ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white)

## 🌟 5. 주요 기능
### 숫자 야구 게임
- 게임 생성: 사용자가 원하는 자릿수로 게임 생성 가능
- 숫자 추측: 스트라이크와 볼 판정을 받아 정답 유추
- 게임 통계: 로그인한 사용자의 게임 기록 저장 및 조회

### 테트리스 게임
- 테트리스 게임 생성: 보드 크기, 초기 레벨 설정 가능
- 블록 조작: 이동, 회전, 드롭, 하드드롭, 홀드 기능
- 점수 시스템: 라인 클리어, 레벨 상승에 따른 점수 계산
- 리더보드: 최고 점수 리더보드 제공

### 사용자 관리
- 회원가입 및 로그인
- JWT 기반 인증 시스템
- 카카오 소셜 로그인
- 사용자 게임 히스토리 관리

## 🧠 6. 기술적 고도화
<div markdown="1">
  <ul>
    <details>
<summary><b>🔹 JWT 기반 인증 시스템 구현</b></summary>

### [ 배경 ]
게임 API에 사용자 인증 시스템을 도입해야 했습니다. 특히 게임 기록 저장, 리더보드 관리 등의 기능을 위해 신뢰할 수 있는 인증 시스템이 필요했습니다.

### 📝 요구사항
- 상태를 저장하지 않는(Stateless) 인증 시스템
- 안전한 사용자 인증 제공
- 토큰 만료 및 갱신 메커니즘
- 소셜 로그인과의 통합 가능성

### 🔧 선택지
- 세션 기반 인증
- JWT 기반 인증
- OAuth2 인증

### ✅ 의사결정 및 이유
JWT 기반 인증 시스템을 선택했습니다:

- **Stateless 특성**: 서버에 상태를 저장할 필요가 없어 확장성이 좋음
- **보안성**: 토큰에 서명을 통한 데이터 무결성 보장
- **유연성**: 액세스 토큰과 리프레시 토큰을 분리하여 보안과 사용자 경험 균형
- **확장성**: 소셜 로그인(카카오)과 통합 용이

### 구현 방식
- 짧은 유효기간의 액세스 토큰(30분)
- 긴 유효기간의 리프레시 토큰(7일)
- 토큰 자동 갱신 미들웨어 구현
- 쿠키 또는 Authorization 헤더를 통한 유연한 토큰 전송
</details>

<details>
<summary><b>🔹 테트리스 게임 동시성 제어</b></summary>

### [ 배경 ]
테트리스 게임에서 사용자의 게임 상태를 안전하게 관리하기 위해 동시성 제어가 필요했습니다. 특히 블록 이동, 점수 계산, 게임 상태 변경 등의 작업이 동시에 이루어질 때 데이터 정합성을 보장해야 했습니다.

### 📝 요구사항
- 각 게임 인스턴스의 독립성 보장
- 동시 요청에 대한 안전한 처리
- 데이터베이스 일관성 유지
- 성능 영향 최소화

### 🔧 선택지
- 낙관적 락(Optimistic Lock)
- 비관적 락(Pessimistic Lock)
- 트랜잭션 격리 수준 조정

### ✅ 의사결정 및 이유
트랜잭션 기반의 접근 방식을 선택했습니다:

- **게임별 격리**: 각 게임은 고유 ID로 식별되어 자연스럽게 격리됨
- **트랜잭션 사용**: 게임 상태 변경은 항상 트랜잭션 내에서 수행
- **데이터베이스 제약 조건**: 유니크 제약 조건을 통한 충돌 방지
- **확장성**: 동시에 여러 게임이 진행되어도 서로 영향을 주지 않음

### 구현 방식
- 게임 상태 변경 작업은 트랜잭션으로 래핑
- 각 게임 이동 요청에 대해 상태 변경 전 검증 로직 실행
- 유효하지 않은 상태 변경 요청에 대한 명확한 오류 응답
</details>

<details>
<summary><b>🔹 Docker 및 CI/CD 파이프라인 구축</b></summary>

### [ 배경 ]
개발과 배포 과정을 자동화하고, 일관된 환경에서 애플리케이션을 실행하기 위한 인프라 구축이 필요했습니다.

### 📝 요구사항
- 개발 및 운영 환경의 일관성
- 자동화된 빌드 및 배포 과정
- 배포 안정성 확보
- 환경 변수 보안 관리

### 🔧 선택지
- 직접 서버 관리 및 수동 배포
- Docker + GitHub Actions
- Kubernetes 기반 배포
- 클라우드 관리형 서비스(AWS ECS, EKS 등)

### ✅ 의사결정 및 이유
Docker와 GitHub Actions를 활용한 CI/CD 파이프라인을 구축했습니다:

- **일관성**: Docker 컨테이너로 개발 및 운영 환경 일관성 확보
- **자동화**: GitHub Actions를 통한 빌드 및 배포 자동화
- **간결성**: 복잡한 오케스트레이션 없이 단일 컨테이너로 서비스 운영
- **보안**: GitHub Secrets를 활용한 환경 변수 보안 관리

### 구현 방식
- Dockerfile을 통한 컨테이너 이미지 정의
- GitHub Actions 워크플로우 구성
- Docker Hub를 통한 이미지 배포
- AWS EC2에서 최신 이미지 자동 배포
</details>
  </ul>
</div>

### 트러블 슈팅
<div markdown="1">
  <ul>
    <details>
    <summary><b>🔹 JWT 토큰 자동 갱신 미들웨어 문제</b></summary>
        
### [ 문제 인식 ]
액세스 토큰이 만료된 후 자동으로 리프레시 토큰을 사용하여 새 액세스 토큰을 발급하는 과정에서, 갱신된 토큰이 응답 헤더에 제대로 설정되지 않는 문제가 발생했습니다.

### 🧪 문제 현상
- 액세스 토큰이 만료되면 클라이언트는 401 오류를 수신
- 미들웨어에서 리프레시 토큰을 처리하지만 새 토큰이 응답에 반영되지 않음
- 클라이언트에서 토큰 갱신 여부를 확인할 수 없음

### [ 문제 원인 ]
- FastAPI 미들웨어의 실행 흐름에서 미들웨어에서 설정한 응답 헤더가 최종 응답에 반영되지 않음
- `await call_next(request)` 이후 응답 객체를 변경하는 방식의 문제

### [ 해결 방법 및 개선 사항 ]
```python
# 수정 전 코드
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # 토큰 검증 및 갱신 로직
    response = await call_next(request)
    response.headers["Authorization"] = f"Bearer {new_access_token}"
    return response
```

```python
# 수정 후 코드
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # 토큰 검증 로직
    if 액세스 토큰 만료 and 리프레시 토큰 유효:
        # 새 액세스 토큰 생성
        request.state.user = {"email": user.email, "id": user.id}
        request.state.new_access_token = new_access_token
    
    response = await call_next(request)
    
    # 요청 상태에서 새 토큰 확인
    if hasattr(request.state, "new_access_token"):
        response.headers["Authorization"] = f"Bearer {request.state.new_access_token}"
    
    return response
```
- `request.state`를 활용하여, 갱신된 토큰 정보를 저장하고 엔드포인트 처리 후 응답 헤더에 설정
- 이를 통해 미들웨어에서 설정한 헤더가 최종 응답에 반영되도록 개선

### ✅ 개선 결과
- 액세스 토큰 만료 시 자동으로 새 토큰을 발급하여 응답 헤더에 포함
- 클라이언트는 응답 헤더에서 새 토큰을 확인하고 저장할 수 있음
- 사용자 경험 개선: 토큰 만료로 인한 401 오류 없이 원활한 서비스 이용 가능
</details>

<details>
<summary><b>🔹 테트리스 블록 홀드 기능 구현 문제</b></summary>

### [ 문제 인식 ]
테트리스 게임에서 블록 홀드 기능을 구현하는 과정에서, 데이터베이스 스키마 변경과 기존 로직 호환성 문제가 발생했습니다.

### 🧪 문제 현상
- 홀드 기능 추가 시 기존 진행 중인 게임에서 오류 발생
- 새로운 필드(`held_piece`, `can_hold`) 추가로 인한 스키마 불일치
- 게임 로직에서 null 값 처리 문제

### [ 문제 원인 ]
- 데이터베이스 모델에 새 필드 추가 후 마이그레이션을 적용했지만, 기존 게임 인스턴스는 해당 필드가 없음
- 새 필드에 대한 예외 처리 로직이 불충분함
- 홀드 기능 관련 파라미터가 API 스키마에 명확히 정의되지 않음

### [ 해결 방법 및 개선 사항 ]
1. **안전한 필드 접근**
```python
# 수정 전 코드
held_piece = json.loads(game.held_piece) if game.held_piece else None
can_hold = game.can_hold

# 수정 후 코드
try:
    held_piece = json.loads(game.held_piece) if game.held_piece else None
except (AttributeError, TypeError):
    held_piece = None

try:
    can_hold = game.can_hold
except AttributeError:
    can_hold = True
```
   - 예외 처리 로직 추가하여 필드 누락 시 기본값 사용

2. **API 스키마 명확화**
```python
# TetrisMoveRequest 스키마 확장
class TetrisMoveRequest(BaseModel):
    move_type: str
    clear_hold: Optional[bool] = False  # 홀드 블록을 비우기 위한 옵션
    skip_store: Optional[bool] = False  # 현재 블록을 홀드에 저장하지 않기 위한 옵션
```
   - TetrisMoveRequest 스키마에 홀드 관련 옵션 추가

3. **홀드 로직 고도화**
   - 홀드 상태에 따른 다양한 케이스 처리
   - 홀드 사용 제한 로직 구현 (한 번 드롭될 때까지 재사용 불가)
   - 홀드 관련 변수를 항상 응답에 포함하도록 수정

### ✅ 개선 결과
- 기존 게임과 새 게임 모두 홀드 기능 정상 작동
- 명확한 API 스키마로 클라이언트 개발 용이
- 다양한 홀드 전략(교체, 비우기, 저장하지 않기 등) 지원
</details>

<details>
<summary><b>🔹 카카오 소셜 로그인 리다이렉트 문제</b></summary>

### [ 문제 인식 ]
카카오 소셜 로그인 구현 과정에서, OAuth 인증 후 프론트엔드로 리다이렉트되는 과정에서 토큰 전달이 제대로 이루어지지 않는 문제가 발생했습니다.

### 🧪 문제 현상
- 카카오 로그인 성공 후 리다이렉트는 정상적으로 수행됨
- 그러나 프론트엔드에서 액세스 토큰을 받지 못하는 문제 발생
- 로그인 정보는 DB에 정상 저장되나 클라이언트 인증 불가

### [ 문제 원인 ]
- 리다이렉트 URL에 토큰을 쿼리 파라미터로 전달하는 방식 사용
- 쿼리 파라미터는 URL 길이 제한과 보안 위험이 있음
- 로깅 과정에서 토큰 전체가 노출되는 보안 취약점 발견

### [ 해결 방법 및 개선 사항 ]
1. **해시 프래그먼트 사용**
```python
# 수정 전 코드
redirect_url = f"{success_uri}?access_token={login_response.access_token}"

# 수정 후 코드
redirect_url = f"{success_uri}#access_token={login_response.access_token}"
```
   - 쿼리 파라미터 대신 해시 프래그먼트(#)를 사용하여 토큰 전달

2. **로깅 보안 강화**
```python
# 수정 전 코드
logger.info(f"Redirecting to: {redirect_url}")

# 수정 후 코드
logger.info(f"Redirecting to: {success_uri}#access_token=...")
```
   - 민감한 정보 로깅 최소화

3. **오류 처리 개선**
   - 상세한 오류 정보 캡처 및 안전한 로깅
   - 클라이언트에 전달되는 오류 메시지 개선

### ✅ 개선 결과
- 해시 프래그먼트를 사용하여 토큰 전달 방식 개선
- 토큰이 URL 이력에 남지 않아 보안 강화
- 오류 발생 시 디버깅을 위한 로깅 개선
- 클라이언트에서 액세스 토큰 정상 수신 및 활용 가능
</details>
  </ul>
</div>

## 🧑‍🤝‍🧑 7. API 문서화 및 사용 방법
### API 문서 접근
- **Swagger UI**: 서버 실행 후 `/docs` 엔드포인트 접속
- **ReDoc**: 서버 실행 후 `/redoc` 엔드포인트 접속
