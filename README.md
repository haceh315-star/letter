# 💌 LetterBox

파스텔 블루 디자인의 편지 주고받기 웹 서비스

---

## 📁 프로젝트 구조

```
letter-site/
├── app.py                  # Flask 앱 전체 (라우트, 모델, 인증)
├── requirements.txt        # Python 패키지
├── vercel.json             # Vercel 배포 설정
├── templates/
│   ├── base.html           # 공통 레이아웃 + 네비게이션
│   ├── home.html           # 홈 (최근 편지 + 통계)
│   ├── write.html          # 편지 쓰기
│   ├── inbox.html          # 받은편지함
│   ├── sent.html           # 보낸편지함
│   ├── view_letter.html    # 편지 상세보기
│   ├── admin.html          # 관리자 대시보드
│   ├── login.html          # 로그인
│   └── register.html       # 회원가입
└── static/
    ├── css/style.css       # 파스텔 블루 디자인 시스템
    └── js/main.js          # 알림 배지 폴링 등
```

---

## 🚀 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 실행 (DB 자동 생성 + admin 계정 생성)
python app.py

# 3. 브라우저에서 열기
# http://localhost:5000
```

**기본 관리자 계정**
- ID: `admin`
- PW: `admin1234`
- 배포 전 반드시 변경하세요!

---

## ☁️ Vercel 배포

### 1. GitHub에 push

```bash
git init
git add .
git commit -m "init letterbox"
git remote add origin https://github.com/YOUR_USERNAME/letter-site.git
git push -u origin main
```

### 2. Vercel에서 연결

1. [vercel.com](https://vercel.com) → New Project
2. GitHub 저장소 Import
3. Framework Preset: **Other** 선택
4. 환경변수 설정 (아래 참고)
5. Deploy!

### 3. 환경변수 (Vercel Dashboard → Settings → Environment Variables)

| 변수명 | 값 |
|---|---|
| `SECRET_KEY` | 랜덤 문자열 (예: `openssl rand -hex 32`) |
| `DATABASE_URL` | PostgreSQL URL (아래 참고) |

### 4. 데이터베이스 (Vercel Postgres 또는 Neon)

Vercel은 서버리스 환경이라 SQLite 파일이 유지되지 않습니다.

**Neon (무료 Postgres) 사용 권장:**
1. [neon.tech](https://neon.tech) 가입
2. 프로젝트 생성 → Connection String 복사
3. `pip install psycopg2-binary` 를 requirements.txt에 추가
4. Vercel 환경변수 `DATABASE_URL`에 붙여넣기

**DATABASE_URL 형식:**
```
postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

### 5. 첫 배포 후 DB 초기화

Vercel 배포 후 한 번만 실행:
```bash
# Vercel CLI로 실행
vercel env pull .env.local
python -c "from app import init_db; init_db()"
```

또는 앱의 첫 요청 시 자동으로 `init_db()`가 실행됩니다.

---

## 🔑 기능 요약

| 기능 | 설명 |
|---|---|
| 회원가입 / 로그인 | 비밀번호 해시 저장 (Werkzeug) |
| 홈 | 최근 받은 편지 5개 + 통계 카드 |
| 편지 쓰기 | 받는 사람 선택 → 제목/내용 작성 |
| 받은편지함 | 안 읽은 편지 강조 + 읽음 처리 자동화 |
| 보낸편지함 | 상대방 읽음 여부 표시 |
| 편지 상세 | 답장하기 / 삭제 |
| 관리자 | 모든 편지 + 회원 목록 확인 |
| 알림 배지 | 30초마다 미읽은 수 자동 갱신 |

---

## 🎨 디자인 토큰

- **Primary**: `#3b96f0` (Sky-500)
- **Surface**: `#f5f9fe`
- **Card**: `#ffffff`
- **Rule**: `#d4e8f7`
- **Font**: Noto Serif KR (제목) + Noto Sans KR (본문)
