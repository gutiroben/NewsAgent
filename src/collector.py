import json
import feedparser
import sqlite3
import os
from datetime import datetime, timedelta, timezone
from time import mktime

class NewsCollector:
    def __init__(self, config_path='config/feeds.json', db_path='data/history.db'):
        self.config_path = config_path
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        """데이터베이스 초기화: 이미 처리한 뉴스 링크를 저장할 테이블 생성"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_history (
                link TEXT PRIMARY KEY,
                title TEXT,
                published_at TEXT,
                collected_at TEXT
            )
        ''')
        self.conn.commit()

    def _load_feeds(self):
        """설정 파일에서 피드 목록 로드"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _is_processed(self, link):
        """이미 수집된 링크인지 확인"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM news_history WHERE link = ?', (link,))
        return cursor.fetchone() is not None

    def _save_to_history(self, link, title, published_at):
        """수집된 뉴스 이력 저장"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO news_history (link, title, published_at, collected_at)
                VALUES (?, ?, ?, ?)
            ''', (link, title, published_at, datetime.now().isoformat()))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass # 이미 존재하는 경우 무시

    def collect(self):
        """
        모든 피드를 순회하며 새로운 뉴스를 수집
        RSS 피드 자체가 최근 N개를 제공하므로 시간 필터링 없이
        DB 중복 체크만으로 수집 여부를 결정함.
        """
        feed_config = self._load_feeds()
        collected_news = []
        
        print("Checking for new news items...")

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
                            
                        # 이미 DB에 있으면 건너뜀
                        if self._is_processed(link):
                            continue

                        # 날짜 파싱 (옵션) - 정렬이나 표기용으로만 사용
                        published_at = datetime.now().isoformat() # 기본값
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            dt = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                            published_at = dt.isoformat()

                        # 무조건 수집 목록에 추가 (DB에 없는 새로운 뉴스이므로)
                        news_item = {
                            'category': category,
                            'source': source_name,
                            'title': entry.get('title', 'No Title'),
                            'link': link,
                            'published_at': published_at,
                            'summary': entry.get('summary', '')
                        }
                        collected_news.append(news_item)
                        self._save_to_history(link, news_item['title'], news_item['published_at'])
                        new_count += 1
                    
                    print(f"Done. ({new_count}/{total_entries} new items)")
                    
                except Exception as e:
                    print(f"Error: {e}")
                    
        return collected_news

    def close(self):
        if self.conn:
            self.conn.close()

# 테스트 실행
if __name__ == "__main__":
    collector = NewsCollector()
    news = collector.collect()
    print(f"\nTotal Collected News: {len(news)}")
    for item in news:
        print(f"[{item['category']}] {item['title']} ({item['source']})")
    collector.close()

