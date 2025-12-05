import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from config import settings

class EmailSender:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER if hasattr(settings, 'SMTP_SERVER') else "smtp.gmail.com"
        self.smtp_port = settings.SMTP_PORT if hasattr(settings, 'SMTP_PORT') else 587
        self.sender_email = settings.EMAIL_SENDER
        self.password = settings.EMAIL_PASSWORD
        
    def send_email(self, recipient_email, subject, html_content, attachment_path=None):
        if not self.sender_email or not self.password:
            raise ValueError("Email credentials are missing in settings.")

        try:
            # 메시지 객체 생성
            msg = MIMEMultipart()
            msg['From'] = f"NewsAgent <{self.sender_email}>"
            msg['To'] = recipient_email
            msg['Reply-To'] = self.sender_email
            msg['Subject'] = subject
            
            # 본문 추가 (HTML)
            msg.attach(MIMEText(html_content, 'html'))
            
            # 파일 첨부 (PDF)
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                
                # 헤더 설정 (파일 이름 등)
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)
                print(f"Attached file: {attachment_path}")
            
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


