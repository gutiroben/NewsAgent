import sys
import os
from datetime import datetime
from src.collector import NewsCollector
from src.summarizer import NewsAnalyst, NewsCurator, ReportBuilder
from src.pdf_builder import PDFBuilder
from src.sender import EmailSender
from config import settings

def main():
    print("=== NewsAgent Started ===")
    
    # 0. 환경변수 체크
    if not settings.GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is missing.")
        sys.exit(1)
    if not settings.EMAIL_SENDER or not settings.EMAIL_PASSWORD:
        print("Error: Email credentials are missing.")
        sys.exit(1)
    
    # 1. News Collection
    print("\n[Step 1] Collecting News...")
    news_list = []
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
    print("\n[Step 2] Analyzing News (Gemini)...")
    analyzed_news = []
    try:
        analyst = NewsAnalyst()
        analyzed_news = analyst.analyze_all(news_list, batch_size=5)
        print(f"\nSuccessfully analyzed {len(analyzed_news)} items.")
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

    # 3. News Curation (Top Topics)
    print("\n[Step 3] Curating Top Topics...")
    topics = []
    try:
        curator = NewsCurator()
        topics = curator.select_top_topics(analyzed_news)
        
        print(f"\nSelected {len(topics)} Top Topics:")
        for idx, topic in enumerate(topics):
            print(f"  [{idx+1}] {topic.get('topic_title')}")
            
    except Exception as e:
        print(f"Error during curation: {e}")
        # 계속 진행 (빈 토픽 리스트)

    # 4. Report Building (HTML & PDF)
    print("\n[Step 4] Building Report (HTML & PDF)...")
    html_content = ""
    pdf_filename = "NewsAgent_Report.pdf"
    try:
        # 4-1. HTML (Top 5 Only)
        builder = ReportBuilder()
        html_content = builder.build_html(topics, analyzed_news)
        print("HTML Generated Successfully.")
        
        # 4-2. PDF (Full Report)
        pdf_builder = PDFBuilder()
        pdf_builder.build_pdf(topics, analyzed_news, pdf_filename)
        print(f"PDF Generated Successfully: {pdf_filename}")
        
    except Exception as e:
        print(f"Error during report building: {e}")
        sys.exit(1)

    # 5. Send Email
    print("\n[Step 5] Sending Email...")
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        subject = f"📢 [NewsAgent] 오늘의 AI 트렌드 리포트 ({today_str})"
        
        sender = EmailSender()
        # PDF 파일 첨부하여 발송
        sender.send_email(settings.EMAIL_RECIPIENT, subject, html_content, attachment_path=pdf_filename)
        
    except Exception as e:
        print(f"Error during email sending: {e}")
        sys.exit(1)

    print("\n=== NewsAgent Finished ===")

if __name__ == "__main__":
    main()
