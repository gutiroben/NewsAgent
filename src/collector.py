import json
import feedparser
import sqlite3
import os
from datetime import datetime, timedelta, timezone
from time import mktime
from zoneinfo import ZoneInfo

# 타겟 기사 추적용 상수
TARGET_ARTICLE_TITLE = "Dario Amodei on the Risk of an A.I. Bubble, Regulation and A.G.I."

class NewsCollector:
    def __init__(self, config_path='config/feeds.json'):
        self.config_path = config_path
        # DB 관련 초기화 제거 (GitHub Actions 환경에서는 일회성 실행이므로)
        # self.db_path = db_path
        # self.conn = None
        # self._init_db()

    # def _init_db(self): ... (Removed)
    
    def _is_target_article(self, title: str) -> bool:
        """타겟 기사인지 확인"""
        return TARGET_ARTICLE_TITLE.lower() in title.lower()
    
    def _load_feeds(self):
        """설정 파일에서 피드 목록 로드"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # def _is_processed(self, link): ... (Removed)
    # def _save_to_history(self, link, title, published_at): ... (Removed)

    def collect(self, lookback_hours=24):
        """
        모든 피드를 순회하며 최근 N시간 이내의 뉴스를 수집
        GitHub Actions 환경에 맞춰 DB 중복 체크 대신 시간 기반 필터링 사용
        
        Args:
            lookback_hours: 수집할 시간 범위 (시간 단위)
                           오늘 07:00 (KST)를 기준으로 lookback_hours 전 시간부터 수집
        """
        feed_config = self._load_feeds()
        collected_news = []
        
        # KST 기준으로 오늘 07:00를 기준으로 정확한 시작 시간 계산
        kst = ZoneInfo("Asia/Seoul")
        now_kst = datetime.now(kst)
        today_07_kst = now_kst.replace(hour=7, minute=0, second=0, microsecond=0)
        cutoff_kst = today_07_kst - timedelta(hours=lookback_hours)
        cutoff_time = cutoff_kst.astimezone(timezone.utc)
        
        print(f"Checking news since: {cutoff_kst.strftime('%Y-%m-%d %H:%M:%S KST')} ({cutoff_time.strftime('%Y-%m-%d %H:%M:%S UTC')})")

        for category_group in feed_config['feeds']:
            category = category_group['category']
            print(f"\nScanning Category: {category}")
            
            for source in category_group['sources']:
                source_name = source['name']
                url = source['url']
                print(f"  - Fetching: {source_name}...", end=" ")
                
                try:
                    feed = feedparser.parse(url)
                    new_count = 0
                    total_entries = len(feed.entries)
                    
                    for entry in feed.entries:
                        link = entry.get('link', '')
                        if not link:
                            continue
                            
                        # 날짜 파싱 및 시간 필터링
                        is_recent = False
                        published_at = datetime.now(timezone.utc).isoformat()
                        
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            dt = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                            published_at = dt.isoformat()
                            if dt > cutoff_time:
                                is_recent = True
                        else:
                            # 날짜 정보가 없으면 일단 가져오거나(True), 스킵(False)
                            # 여기서는 안전하게 스킵하거나, 최근 5개만 가져오는 로직을 추가할 수 있음.
                            # 이번에는 날짜 없으면 스킵으로 처리
                            pass

                        if is_recent:
                            title = entry.get('title', 'No Title')
                            news_item = {
                                'category': category,
                                'source': source_name,
                                'title': title,
                                'link': link,
                                'published_at': published_at,
                                'summary': entry.get('summary', '')
                            }
                            collected_news.append(news_item)
                            new_count += 1
                            
                            # 타겟 기사 발견 시 로그
                            if self._is_target_article(title):
                                print(f"\n[TARGET] Found target article in collection!")
                                print(f"[TARGET] Title: {title}")
                                print(f"[TARGET] Source: {source_name}")
                                print(f"[TARGET] Link: {link}")
                                print(f"[TARGET] Index in collected_news: {len(collected_news) - 1}")
                    
                    print(f"Done. ({new_count}/{total_entries} recent items)")
                    
                except Exception as e:
                    print(f"Error: {e}")
                    
        return collected_news

    def close(self):
        pass

# 테스트 실행
if __name__ == "__main__":
    collector = NewsCollector()
    news = collector.collect()
    print(f"\nTotal Collected News: {len(news)}")
    for item in news:
        print(f"[{item['category']}] {item['title']} ({item['source']})")
    collector.close()

