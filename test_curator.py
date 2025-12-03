import sqlite3
import json
from src.summarizer import NewsCurator

def test_curator():
    print("Testing NewsCurator...")
    
    # 1. DB에서 뉴스 로드 (최근 24시간 시뮬레이션)
    # 실제로는 DB에 있는 모든 걸 가져오거나, 특정 개수만큼 가져옵니다.
    conn = sqlite3.connect('data/history.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 테스트를 위해 최신 30개만 가져와 봅니다.
    cursor.execute("SELECT * FROM news_history ORDER BY collected_at DESC LIMIT 30")
    rows = cursor.fetchall()
    conn.close()
    
    news_list = []
    for row in rows:
        news_list.append({
            "title": row['title'],
            "source": "Unknown", # DB 스키마에 source가 없다면 임시 처리, 있다면 추가 필요
            "link": row['link']
        })
        
    if not news_list:
        print("No news found in DB. Run collector.py first.")
        return

    print(f"Loaded {len(news_list)} news items from DB.")

    # 2. Curator 실행
    curator = NewsCurator()
    topics = curator.select_top_topics(news_list)
    
    # 3. 결과 출력
    print(f"\n=== Curated Topics ({len(topics)}) ===")
    for t in topics:
        print(f"\nTopic: {t['topic']}")
        print(f"Reason: {t['reason']}")
        print(f"Related Articles ({len(t['related_news_indices'])}):")
        for idx in t['related_news_indices']:
            # 인덱스 범위 체크
            if 0 <= idx < len(news_list):
                print(f"  - {news_list[idx]['title']}")
            else:
                print(f"  - [Invalid Index {idx}]")

if __name__ == "__main__":
    test_curator()

