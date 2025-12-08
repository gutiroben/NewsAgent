import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from src.collector import NewsCollector
from src.analyst import NewsAnalyst
from src.curator import NewsCurator
from src.html_builder import ReportBuilder
from src.pdf_builder import PDFBuilder
from src.sender import EmailSender
from config import settings

def main():
    # 테스트 모드 확인
    is_test_mode = getattr(settings, 'TEST_MODE', False)
    if is_test_mode:
        print("=== NewsAgent Started (TEST MODE) ===")
        print("[TEST MODE] Test mode is enabled. Reports will be sent to test channel.")
    else:
        print("=== NewsAgent Started ===")
    
    # 0. 환경변수 체크
    if not settings.GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is missing.")
        sys.exit(1)
    if not settings.EMAIL_SENDER or not settings.EMAIL_PASSWORD:
        print("Error: Email credentials are missing.")
        sys.exit(1)
    
    # 타겟 기사 추적
    from src.collector import TARGET_ARTICLE_TITLE
    
    def is_target_article(title: str) -> bool:
        return TARGET_ARTICLE_TITLE.lower() in title.lower()
    
    # 1. News Collection
    print("\n[Step 1] Collecting News...")
    news_list = []
    try:
        collector = NewsCollector()
        news_list = collector.collect() 
        print(f"\nTotal News Collected: {len(news_list)}")
        
        # 타겟 기사 확인
        target_found_in_collection = False
        for idx, news in enumerate(news_list):
            if is_target_article(news['title']):
                target_found_in_collection = True
                print(f"\n[TRACK] Step 1: Target article found at index {idx}")
                print(f"[TRACK] Step 1: Title: {news['title']}")
                break
        
        if not target_found_in_collection:
            print(f"[WARNING] Step 1: Target article NOT found in collection!")
        
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
        # settings.BATCH_SIZE (기본 3) 사용
        batch_size = getattr(settings, 'BATCH_SIZE', 3)
        analyzed_news = analyst.analyze_all(news_list, batch_size=batch_size)
        print(f"\nSuccessfully analyzed {len(analyzed_news)} items.")
        
        # 타겟 기사 분석 결과 확인
        target_found_in_analyzed = False
        for idx, news in enumerate(analyzed_news):
            if is_target_article(news.get('title', '')):
                target_found_in_analyzed = True
                print(f"\n[TRACK] Step 2: Target article found in analyzed_news at index {idx}")
                print(f"[TRACK] Step 2: Has title_korean: {bool(news.get('title_korean'))}")
                print(f"[TRACK] Step 2: Has core_summary: {bool(news.get('core_summary'))}")
                print(f"[TRACK] Step 2: Has detailed_explanation: {bool(news.get('detailed_explanation'))}")
                break
        
        if not target_found_in_analyzed:
            print(f"[ERROR] Step 2: Target article NOT found in analyzed_news!")
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)

    # 3. News Curation (Top Articles) - B2B 관점
    print("\n[Step 3] Curating Top Articles (Samsung MX B2B Dev Group Perspective)...")
    top5_articles = []
    try:
        curator = NewsCurator()
        top5_articles = curator.select_top_articles(analyzed_news)
        
        print(f"\nSelected {len(top5_articles)} Top Articles:")
        target_in_top5 = False
        for idx, article in enumerate(top5_articles):
            title = article.get('title_korean', article['title'])
            print(f"  [{idx+1}] {title}")
            if is_target_article(article.get('title', '')):
                target_in_top5 = True
                print(f"\n[TRACK] Step 3: Target article is in Top 5!")
                print(f"[TRACK] Step 3: Position: {idx+1}")
                print(f"[TRACK] Step 3: title_korean: {title}")
                print(f"[TRACK] Step 3: Has core_summary: {bool(article.get('core_summary'))}")
                print(f"[TRACK] Step 3: Has detailed_explanation: {bool(article.get('detailed_explanation'))}")
        
        if not target_in_top5:
            print(f"[TRACK] Step 3: Target article is NOT in Top 5")
            
    except Exception as e:
        print(f"Error during curation: {e}")
        # 계속 진행 (빈 토픽 리스트)

    # 3.5. B2B Insights Analysis (Top5 기반)
    print("\n[Step 3.5] Analyzing B2B Insights from Top 5 Articles...")
    b2b_insights = {}
    try:
        from src.b2b_insights import B2BInsightsAnalyzer
        insights_analyzer = B2BInsightsAnalyzer()
        b2b_insights = insights_analyzer.analyze_insights(top5_articles)
        print("B2B Insights Generated Successfully.")
        
    except Exception as e:
        print(f"Error during B2B insights analysis: {e}")
        # 계속 진행 (빈 인사이트)

    # 4. Report Building (HTML & PDF)
    print("\n[Step 4] Building Report (HTML & PDF)...")
    html_content = ""
    # 한국 시간대 명시적 사용
    kst = ZoneInfo("Asia/Seoul")
    today_str = datetime.now(kst).strftime("%Y-%m-%d")
    pdf_filename = f"NewsAgent_Report_{today_str}.pdf"
    try:
        # 4-1. HTML (B2B Insights + Top 5)
        builder = ReportBuilder()
        html_content = builder.build_html(top5_articles, analyzed_news, b2b_insights)
        print("HTML Generated Successfully.")
        
        # 4-2. PDF (Full Report with TOC)
        pdf_builder = PDFBuilder()
        pdf_builder.build_pdf(top5_articles, analyzed_news, pdf_filename, b2b_insights)
        print(f"PDF Generated Successfully: {pdf_filename}")
        
    except Exception as e:
        print(f"Error during report building: {e}")
        sys.exit(1)

    # 5. Send Email & Slack
    print("\n[Step 5] Sending Report...")
    try:
        # today_str은 Step 4에서 이미 생성됨
        is_test_mode = getattr(settings, 'TEST_MODE', False)
        
        if is_test_mode:
            subject = f"🧪 [TEST MODE] NewsAgent 리포트 ({today_str})"
            print("[TEST MODE] Using test mode subject prefix")
        else:
            subject = f"📢 [NewsAgent] 오늘의 AI 트렌드 리포트 ({today_str})"
        
        sender = EmailSender()
        
        # 테스트 모드일 때는 테스트용 슬랙 채널로만 발송
        if is_test_mode:
            test_slack_email = getattr(settings, 'TEST_SLACK_CHANNEL_EMAIL', None)
            if test_slack_email:
                print(f"[TEST MODE] Sending to test Slack channel: {test_slack_email}")
                sender.send_email(test_slack_email, subject, html_content, attachment_path=pdf_filename)
                print(f"[TEST MODE] Test report sent successfully to {test_slack_email}")
            else:
                print("[TEST MODE] Warning: TEST_SLACK_CHANNEL_EMAIL is not set. Skipping test send.")
        else:
            # 일반 모드: 기존 로직 유지
            # 이메일 발송 (SEND_TO_EMAIL이 true인 경우)
            if settings.SEND_TO_EMAIL:
                if not settings.EMAIL_RECIPIENT:
                    print("Warning: EMAIL_RECIPIENT is not set. Skipping email.")
                else:
                    sender.send_email(settings.EMAIL_RECIPIENT, subject, html_content, attachment_path=pdf_filename)
                    print(f"Email sent successfully to {settings.EMAIL_RECIPIENT}")
            
            # 슬랙 채널 발송 (SEND_TO_SLACK이 true인 경우)
            if settings.SEND_TO_SLACK:
                if not settings.SLACK_CHANNEL_EMAIL:
                    print("Warning: SLACK_CHANNEL_EMAIL is not set. Skipping Slack.")
                else:
                    sender.send_email(settings.SLACK_CHANNEL_EMAIL, subject, html_content, attachment_path=pdf_filename)
                    print(f"Slack message sent successfully to {settings.SLACK_CHANNEL_EMAIL}")
            
            # 둘 다 false인 경우 경고
            if not settings.SEND_TO_EMAIL and not settings.SEND_TO_SLACK:
                print("Warning: Both SEND_TO_EMAIL and SEND_TO_SLACK are false. No report sent.")
        
    except Exception as e:
        print(f"Error during sending: {e}")
        sys.exit(1)

    print("\n=== NewsAgent Finished ===")

if __name__ == "__main__":
    main()
