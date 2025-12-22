import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")  # 환경변수가 있으면 사용, 없으면 기본값

# Email Settings
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

# Test Mode Settings
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"  # 테스트 모드 활성화 여부 (기본값: false)
TEST_SLACK_CHANNEL_EMAIL = os.getenv("TEST_SLACK_CHANNEL_EMAIL")  # 테스트용 슬랙 채널 이메일 (기본값: None)

# Email Delivery Settings (발송 대상 설정)
SEND_TO_EMAIL = False  # 이메일 발송 여부
SEND_TO_SLACK = True   # 슬랙 채널 발송 여부

# Slack Channel Email (슬랙 채널 이메일 주소 - GitHub Secret에서 설정)
SLACK_CHANNEL_EMAIL = os.getenv("SLACK_CHANNEL_EMAIL")

# Collection Settings
NEWS_LOOKBACK_HOURS = 24
BATCH_SIZE = 1  # 개별 처리 (기사 하나씩 분석)

