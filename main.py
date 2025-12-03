import sys
import os
from src.collector import NewsCollector
from src.summarizer import NewsAnalyst
from dotenv import load_dotenv

# 로컬 실행 시 .env 로드 (GitHub Actions에서는 무시됨)
load_dotenv()

def main():
    print("=== NewsAgent Started ===")
    
    # 0. 환경변수 체크
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY is missing.")
        sys.exit(1)
    
    # 1. News Collection
    print("\n[Step 1] Collecting News...")
    try:
        collector = NewsCollector()
        news_list = collector.collect() # 기본 24시간
        
        print(f"\nTotal News Collected: {len(news_list)}")
        
        if not news_list:
            print("No news found today. Exiting.")
            return

    except Exception as e:
        print(f"Error during collection: {e}")
        sys.exit(1)

    # 2. News Analysis
    print("\n[Step 2] Analyzing News (Gemini Pro)...")
    try:
        analyst = NewsAnalyst()
        # GitHub Actions 시간 제한 및 API 할당량 고려하여 
        # 너무 많으면 앞에서 자르거나 그대로 다 넣음. (Batch 처리가 되어있으므로 안전)
        # 테스트 단계이므로 로그를 위해 개수 제한을 두지 않음.
        
        analyzed_news = analyst.analyze_all(news_list, batch_size=5)
        print(f"\nSuccessfully analyzed {len(analyzed_news)} items.")
        
        # 분석 결과 미리보기 (상위 3개)
        print("\n--- Analysis Result Preview ---")
        for item in analyzed_news[:3]:
            print(f"\n[Title] {item.get('title_korean', item['title'])}")
            print(f"[Summary] {item.get('one_line_summary', 'N/A')}")
            print(f"[Points] {item.get('analysis', 'N/A')}")
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

    print("\n=== NewsAgent Finished ===")

if __name__ == "__main__":
    main()
