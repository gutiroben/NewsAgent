import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import settings

class EmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = settings.EMAIL_SENDER
        self.password = settings.EMAIL_PASSWORD
        
    def send_email(self, recipient_email, subject, html_content):
        if not self.sender_email or not self.password:
            raise ValueError("Email credentials are missing in settings.")

        try:
            # 메시지 객체 생성
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # 본문 추가 (HTML)
            msg.attach(MIMEText(html_content, 'html'))
            
            # SMTP 서버 연결
            print(f"Connecting to SMTP server ({self.smtp_server})...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls() # 보안 연결
                server.login(self.sender_email, self.password)
                server.send_message(msg)
                
            print(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            raise e

