import requests
from groq import Groq
from datetime import datetime, timedelta
import os
import time
import schedule
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re

load_dotenv()

# === [설정: .env 파일에서 자동으로 로드] ===
NAVER_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_SECRET = os.getenv("NAVER_CLIENT_SECRET")
GROQ_KEY = os.getenv("GROQ_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")  # DB_ID 대신 Page_ID 사용

KEYWORDS = ["피지컬 AI", "전북 피지컬 AI", "전북테크노파크", "경남 피지컬 AI", "NIPA 피지컬 AI"]
DISPLAY_COUNT = 3  # 키워드당 수집할 뉴스 개수
EXCLUDE_KEYWORD = "주식"
# ========================================

client = Groq(api_key=GROQ_KEY)

def get_news():
    """네이버 뉴스 API를 통해 뉴스를 수집합니다."""
    all_news = []
    seen_links = set()
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    print("뉴스 수집을 시작합니다...")
    for kw in KEYWORDS:
        url = f"https://openapi.naver.com/v1/search/news.json?query={kw}&display={DISPLAY_COUNT * 2}&sort=date"
        try:
            res = requests.get(url, headers=headers).json()
            
            count = 0
            if 'items' in res:
                for item in res['items']:
                    if count >= DISPLAY_COUNT:
                        break
                    
                    link = item['link']
                    title = item['title']
                    desc = item['description']
                    
                    # 1. 중복 제거
                    if link in seen_links:
                        continue
                    
                    # 2. 제외 키워드 필터링
                    if EXCLUDE_KEYWORD in title or EXCLUDE_KEYWORD in desc:
                        continue
                    
                    # HTML 태그 제거
                    clean_title = title.replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                    clean_desc = desc.replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                    
                    all_news.append({
                        "title": clean_title,
                        "link": link,
                        "desc": clean_desc,
                        "pubDate": item.get('pubDate', '')
                    })
                    seen_links.add(link)
                    count += 1
        except Exception as e:
            print(f"  키워드 '{kw}' 검색 중 오류: {e}")
                
    return all_news

def get_press_name(url):
    """기사 URL에서 언론사 이름을 추출합니다."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')
        
        press = None
        
        # 메타 태그 우선 확인
        meta_site = soup.find('meta', property='og:site_name')
        if meta_site:
            press = meta_site.get('content')
            
        if not press:
            meta_twitter = soup.find('meta', name='twitter:site')
            if meta_twitter:
                press = meta_twitter.get('content')
        
        if not press and soup.title:
            title_text = soup.title.string
            # 일반적인 "제목 - 언론사" 패턴 시도
            separators = [" - ", " : ", " | "]
            for sep in separators:
                if sep in title_text:
                    press = title_text.split(sep)[-1]
                    break

        if press:
            return press.strip()
    except:
        pass # 조용히 실패
    
    return "언론사 미상"

def summarize(title, desc):
    """Groq API를 사용하여 뉴스를 요약합니다."""
    prompt = (
        f"너는 기업 경영지원팀의 뉴스 요약 전문가야. 다음 뉴스 내용을 바탕으로 보고용 3줄 요약을 작성해줘.\n"
        f"규칙:\n"
        f"1. 한국어로 작성.\n"
        f"2. 인사말 생략, 본론만.\n"
        f"3. 특수문자 최소화.\n"
        f"4. 각 줄은 명확한 문장으로.\n\n"
        f"5. 줄 바꿈 하지말고 뛰어쓰기로 줄을 구분해줘.\n\n"
        f"제목: {title}\n"
        f"내용: {desc}"
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"  요약 생성 실패: {e}")
        return "요약 내용을 생성할 수 없습니다."

def extract_keywords(title, desc):
    """Groq API를 사용하여 뉴스에서 핵심 키워드 2-3개를 추출합니다."""
    prompt = (
        f"다음 뉴스 내용에서 핵심 키워드 2~3개를 추출해줘.\n"
        f"규칙:\n"
        f"1. 한국어로 작성.\n"
        f"2. 각 키워드는 '#' 기호와 함께 해시태그 형식으로.\n"
        f"3. 키워드는 공백으로 구분.\n"
        f"4. 예시: #전북 #피지컬AI #실증센터 #NIPA #전북테크노파크\n"
        f"5. 다른 설명 없이 해시태그만 출력.\n\n"
        f"제목: {title}\n"
        f"내용: {desc}"
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        keywords = completion.choices[0].message.content.strip()
        # 혹시 불필요한 텍스트가 포함되었을 경우를 대비해 # 기호가 있는 부분만 추출
        if '#' in keywords:
            return keywords
        else:
            return "#피지컬AI #AI동향"  # 기본값
    except Exception as e:
        print(f"  키워드 추출 실패: {e}")
        return "#피지컬AI #AI동향"  # 기본값

def create_notion_blocks(news_items):
    """수집된 뉴스 아이템을 Notion 블록 구조로 변환합니다."""
    children = []
    
    for item in news_items:
        title = item['title']
        link = item['link']
        press = item['press']
        summary = item['summary']
        tags = item.get('keywords', "#피지컬AI #AI동향")  # 동적 태그 사용
        
        # 블록 1: 2개 열 레이아웃 (제목 | 언론사 + 태그)
        column_list_block = {
            "object": "block",
            "type": "column_list",
            "column_list": {
                "children": [
                    {
                        "object": "block",
                        "type": "column",
                        "column": {
                            "children": [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {"content": title, "link": {"url": link}},
                                                "annotations": {"bold": True}
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "column",
                        "column": {
                            "children": [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {"content": press},
                                                "annotations": {"bold": True}
                                            }
                                        ]
                                    }
                                },
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {
                                                "type": "text",
                                                "text": {"content": tags},
                                                "annotations": {"bold": True}
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
        children.append(column_list_block)
        
        # 블록 2: 구분선 (2개 열 블록과 본문 사이)
        divider_block = {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
        children.append(divider_block)
        
        # 블록 3: 요약 내용
        summary_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": summary}
                    }
                ]
            }
        }
        children.append(summary_block)
        
        # 블록 4: 본문 뒤 구분선
        divider_block_end = {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
        children.append(divider_block_end)
        
    return children

def send_daily_report_to_page(news_items):
    """Notion 페이지에 일일 보고서를 토글 블록으로 추가합니다."""
    if not news_items:
        print("전송할 뉴스가 없습니다.")
        return

    today_str = datetime.now().strftime("%Y%m%d")
    print(f"Notion 페이지({NOTION_PAGE_ID})에 '{today_str}' 작성 중...")
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # 1단계: 빈 토글 블록 생성
    toggle_block = {
        "object": "block",
        "type": "toggle", 
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": today_str}}]
        }
    }
    
    url = f"https://api.notion.com/v1/blocks/{NOTION_PAGE_ID}/children"
    data = {"children": [toggle_block]}
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"토글 블록 생성 실패: {response.status_code}")
        print(response.text)
        return
    
    # 생성된 토글 블록의 ID 추출
    toggle_id = response.json()['results'][0]['id']
    print(f"토글 블록 생성 성공 (ID: {toggle_id})")
    
    # 2단계: 토글 안에 구분선 먼저 추가
    divider_first = {
        "object": "block",
        "type": "divider",
        "divider": {}
    }
    
    # 3단계: 뉴스 블록 생성
    news_blocks = create_notion_blocks(news_items)
    
    # 구분선을 맨 앞에 추가
    all_blocks = [divider_first] + news_blocks
    
    url = f"https://api.notion.com/v1/blocks/{toggle_id}/children"
    data = {"children": all_blocks}
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("Notion 전송 성공!")
    else:
        print(f"뉴스 블록 추가 실패: {response.status_code}")
        print(response.text)

def run_job():
    print("\n" + "=" * 50)
    print(f"작업 시작: {datetime.now()}")
    
    # 1. 뉴스 수집
    raw_items = get_news()
    if not raw_items:
        print("새로운 뉴스가 없습니다.")
        return
    
    print(f"총 {len(raw_items)}개의 뉴스 수집 완료. 상세 처리 시작...")
    
    processed_items = []
    
    # 2. 각 뉴스 상세 처리 (요약, 언론사, 키워드 추출)
    for i, item in enumerate(raw_items, 1):
        print(f"[{i}/{len(raw_items)}] 처리 중: {item['title'][:30]}...")
        
        # 요약
        summary = summarize(item['title'], item['desc'])
        
        # 언론사
        press = get_press_name(item['link'])
        
        # 키워드 추출
        keywords = extract_keywords(item['title'], item['desc'])
        
        item['summary'] = summary
        item['press'] = press
        item['keywords'] = keywords
        processed_items.append(item)
    
    # 3. Notion 페이지로 전송
    send_daily_report_to_page(processed_items)
    
    print("모든 작업 완료")
    print("=" * 50)

def main():
    print("뉴스 봇 시작...")
    print("=" * 50)
    
    # 시작 시 즉시 1회 실행
    print("초기 실행을 시작합니다.")
    run_job()
    
    print("\n스케줄러 대기 중... (평일 매일 09:00 자동 실행)")
    print("프로그램을 종료하려면 Ctrl+C를 누르세요.")
    print("=" * 50)

    # 평일 오전 9시 스케줄 등록
    schedule.every().monday.at("09:00").do(run_job)
    schedule.every().tuesday.at("09:00").do(run_job)
    schedule.every().wednesday.at("09:00").do(run_job)
    schedule.every().thursday.at("09:00").do(run_job)
    schedule.every().friday.at("09:00").do(run_job)

    # 스케줄러 실행
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()  # 즉시 실행 + 스케줄러 활성화


