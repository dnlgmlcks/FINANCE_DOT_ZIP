💰 FINANCE_DOT_ZIP (Frontend)
Team RETURNS가 개발하는 AI 기반 실시간 금융 데이터 분석 및 추천 서비스의 프론트엔드 저장소입니다.

🛠️ Tech Stack
Framework: React

Build Tool: Vite (최신 표준 환경)

Language: JavaScript (JSX)

📂 Project Structure
Vite의 기본 구조를 프로젝트 성격에 맞게 최적화하여 관리합니다.

Plaintext
frontend/
├── node_modules/       # 외부 라이브러리 부품
├── public/             # 파비콘, 아이콘 등 정적 자산
├── src/
│   ├── assets/         # 로고, 이미지 파일
│   ├── components/     # 재사용 가능한 UI 부품 (Header, MainContent, Footer 등)
│   ├── App.jsx         # 컴포넌트 조립 및 메인 로직
│   ├── App.css         # 메인 레이아웃 스타일
│   ├── main.jsx        # 리액트 앱 시작점
│   └── index.css       # 전체 공통 스타일 (폰트 등)
├── .gitignore          # Git 업로드 제외 목록
├── eslint.config.js    # 코드 문법 및 스타일 검사 설정
├── index.html          # 메인 HTML 도화지
├── package.json        # 프로젝트 설계도 및 실행 명령어
└── vite.config.js      # Vite 설정 파일

🚀 Getting Started
1. 의존성 설치
프로젝트에 필요한 부품들을 먼저 설치해야 합니다.

터미널
npm install
2. 개발 서버 실행
로컬 환경에서 실시간 수정 사항을 확인하며 개발합니다.

터미널
npm run dev
실행 후 터미널에 뜨는 http://localhost:5173 주소로 접속하세요.