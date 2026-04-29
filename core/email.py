# For sending OTP emails to users. In development, it prints the OTP to the console instead of sending an email, so you can test the flow without needing a real email account or SMTP server. In production, it uses SMTP credentials from environment variables to send real emails. If SMTP credentials are not set, it will warn and only print the OTP to the console.
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_otp_email(to_email: str, otp_code: str):
    print(f"\n[DEV MODE] OTP for {to_email} is: {otp_code}\n")
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("[WARN] SMTP credentials not set. OTP printed to console only.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = to_email
        msg["Subject"] = "Safe-Steps: Your Verification Code"
        
        body = f"Your verification code is: {otp_code}\nThis code will expire in 10 minutes."
        msg.attach(MIMEText(body, "plain"))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"OTP email sent to {to_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
