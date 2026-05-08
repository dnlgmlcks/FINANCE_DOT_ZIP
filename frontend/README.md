💰 FINANCE_DOT_ZIP (Frontend)
Team FINANCE_DOT_ZIP이 개발하는 AI 기반 실시간 금융 데이터 분석 및 추천 서비스의 프론트엔드 저장소입니다.

🛠️ Tech Stack
Framework: React

Build Tool: Vite (최신 표준 환경)

Language: JavaScript (JSX)

📂 Project Structure
Vite의 기본 구조를 프로젝트 성격에 맞게 최적화하여 관리합니다.

```plaintext
frontend/
├── node_modules/           # 외부 라이브러리 부품
├── public/                 # 파비콘, 아이콘 등 정적 자산
├── src/
│   ├── components/         # 재사용 가능한 UI 부품
│   │   ├── ChatArea/       # AI 챗봇 패널
│   │   │   ├── AIchatpanel.jsx
│   │   │   └── AIchatpanel.css
│   │   ├── Header.jsx      # 상단 헤더
│   │   ├── Header.css
│   │   ├── Footer.jsx      # 하단 푸터
│   │   ├── SearchBox.jsx   # 종목 검색 입력창
│   │   ├── MainContent.jsx # 메인 콘텐츠 영역
│   │   └── Report.jsx      # 재무 리포트 컴포넌트
│   ├── layouts/            # 페이지 공통 레이아웃
│   │   ├── MainLayout.jsx  # 탭 + 본문 + 챗봇 패널 구조
│   │   └── MainLayout.css
│   ├── pages/              # 탭별 페이지 컴포넌트
│   │   ├── NewsAnalysis/   # 뉴스 분석 페이지
│   │   │   ├── components/ # 신호 목록, 뉴스 요약, 출처 등 하위 컴포넌트
│   │   │   ├── index.jsx
│   │   │   └── NewsAnalysis.css
│   │   ├── Report/         # 재무 보고서 페이지
│   │   │   └── index.jsx
│   │   └── Disclosure/     # 공시 분석 페이지
│   │       └── index.jsx
│   ├── util/               # 공통 유틸리티
│   │   └── common-util.js  # API 통신 등 공통 함수
│   ├── App.jsx             # 컴포넌트 조립 및 메인 로직
│   ├── App.css             # 메인 레이아웃 스타일
│   ├── main.jsx            # 리액트 앱 시작점
│   └── index.css           # 전체 공통 스타일 (폰트, 색상 변수 등)
├── .gitignore              # Git 업로드 제외 목록
├── eslint.config.js        # 코드 문법 및 스타일 검사 설정
├── index.html              # 메인 HTML 도화지
├── package.json            # 프로젝트 설계도 및 실행 명령어
└── vite.config.js          # Vite 설정 파일
```

🚀 Getting Started
1. 의존성 설치
프로젝트에 필요한 부품들을 먼저 설치해야 합니다.

```
npm install
```

2. 개발 서버 실행
로컬 환경에서 실시간 수정 사항을 확인하며 개발합니다.

```
npm run dev
```
