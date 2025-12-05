import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = "gemini-2.5-flash"  # User requested version

# Email Settings
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

# Email Delivery Settings (발송 대상 설정)
SEND_TO_EMAIL = False  # 이메일 발송 여부
SEND_TO_SLACK = True   # 슬랙 채널 발송 여부

# Slack Channel Email (슬랙 채널 이메일 주소 - GitHub Secret에서 설정)
SLACK_CHANNEL_EMAIL = os.getenv("SLACK_CHANNEL_EMAIL")

# Collection Settings
NEWS_LOOKBACK_HOURS = 24
BATCH_SIZE = 3  # 심층 분석을 위해 배치 사이즈 축소 (5 -> 3)

