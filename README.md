# News Bot for Notion
전북 테크노파크 피지컬 AI팀의 자동화 금일 동향보고 프로그램입니다.
매일 반복되는 수동 동향 보고 업무를 자동화하여 리소스를 절감하고, 데이터 기반의 팀 내 정보 공유 문화를 정착시키기 위해 기획되었습니다. 
네이버 뉴스 API를 통해 팀의 핵심 키워드와 관련된 최신 정보를 실시간으로 수집하고, Groq AI를 활용해 핵심 내용을 요약함으로써 정보 습득의 가독성을 높였습니다. 
최종적으로 모든 데이터는 노션(Notion) 페이지로 자동 전송되어 팀원 누구나 언제 어디서든 당일의 기술 및 시장 동향을 한눈에 파악할 수 있는 유연한 협업 환경을 제공합니다.

## 주요 기능

- **자동 뉴스 수집**: 네이버 뉴스 API를 통해 설정된 키워드 기반 최신 뉴스 수집
- **AI 요약**: Groq API를 사용하여 뉴스 내용을 3줄 요약으로 압축
- **키워드 추출**: 각 뉴스에서 핵심 키워드 2-3개를 자동 추출하여 태그 생성
- **언론사 자동 인식**: 웹 스크래핑을 통해 실제 언론사명 추출
- **중복 제거**: 동일한 뉴스 링크 및 특정 키워드(예: 주식) 필터링
- **Notion 연동**: 수집된 뉴스를 Notion 페이지에 토글 블록으로 자동 추가
- **스케줄링**: 평일 오전 9시 자동 실행 (schedule 라이브러리 사용)

## 기술 스택

- **Python 3.x**
- **네이버 뉴스 검색 API**: 뉴스 데이터 수집
- **Groq API**: AI 기반 요약 및 키워드 추출
- **Notion API**: 보고서 자동 작성
- **BeautifulSoup4**: 웹 스크래핑 (언론사명 추출)
- **Schedule**: 작업 스케줄링

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd 동향보고
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력합니다:

```env
# 네이버 API
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Groq API
GROQ_API_KEY=your_groq_api_key

# Notion API
NOTION_TOKEN=your_notion_integration_token
NOTION_PAGE_ID=your_notion_page_id
```

#### API 키 발급 방법

- **네이버 API**: [네이버 개발자 센터](https://developers.naver.com/apps/#/register)에서 애플리케이션 등록
- **Groq API**: [Groq Console](https://console.groq.com/)에서 API 키 발급
- **Notion API**: [Notion Integrations](https://www.notion.so/my-integrations)에서 통합 생성 후 페이지 연결

## 사용 방법

### 즉시 실행 (테스트)

```bash
python simple_news_bot.py
```

또는 Windows에서:

```bash
run.bat
```

### 스케줄러 실행 (자동화)

`simple_news_bot.py` 파일의 마지막 부분을 다음과 같이 수정:

```python
if __name__ == "__main__":
    main()  # 스케줄러 실행 (평일 09:00 자동 실행)
    # run_job()  # 즉시 실행 (개발/테스트용)
```

## 설정 커스터마이징

`simple_news_bot.py` 파일에서 다음 설정을 수정할 수 있습니다:

```python
# 검색 키워드 설정
KEYWORDS = ["피지컬 AI", "전북 피지컬 AI", "전북테크노파크", "경남 피지컬 AI", "NIPA 피지컬 AI"]

# 키워드당 수집할 뉴스 개수
DISPLAY_COUNT = 3

# 제외할 키워드
EXCLUDE_KEYWORD = "주식"
```

## Notion 출력 형식

뉴스는 다음과 같은 구조로 Notion에 저장됩니다:

```
▼ 20260205 (토글)
  ─────────────────────────
  제목 (링크)          │ 언론사
                       │ #키워드1 #키워드2
  ─────────────────────────
  요약 내용 (3줄)
  ─────────────────────────
```

## 프로젝트 구조

```
동향보고/
├── simple_news_bot.py    # 메인 봇 스크립트
├── requirements.txt      # Python 의존성 목록
├── .env                  # 환경 변수 (Git에 포함되지 않음)
├── run.bat              # Windows 실행 스크립트
└── README.md            # 프로젝트 문서
```

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트는 언제든 환영합니다.
