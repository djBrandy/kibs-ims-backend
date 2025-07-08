import smtplib
from email.mime.text import MIMEText
import africastalking # type: ignore
import os

def send_email(to_email, subject, body):
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_email], msg.as_string())

def send_sms_africastalking(phone, message):
    africastalking.initialize(os.environ.get("AT_USERNAME"), os.environ.get("AT_API_KEY"))
    sms = africastalking.SMS
    sms.send(message, [phone])