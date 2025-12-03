import sys
from src.collector import NewsCollector

def main():
    print("=== NewsAgent Started ===")
    
    # 1. News Collection
    print("\n[Step 1] Collecting News...")
    try:
        collector = NewsCollector()
        # GitHub Actions 테스트를 위해 24시간(기본값) 수집
        news_list = collector.collect()
        
        print(f"\nTotal News Collected: {len(news_list)}")
        
        if not news_list:
            print("No news found today. Exiting.")
            return

        # 수집 결과 미리보기
        print("\n--- Collected News Preview ---")
        for idx, news in enumerate(news_list[:5]): # 상위 5개만 출력
            print(f"[{idx+1}] {news['title']} ({news['source']})")
        if len(news_list) > 5:
            print(f"... and {len(news_list) - 5} more.")

    except Exception as e:
        print(f"Error during collection: {e}")
        sys.exit(1)

    print("\n=== NewsAgent Finished ===")

if __name__ == "__main__":
    main()
