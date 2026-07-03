import os
import random
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp(receiver_email, otp):

    sender_email = os.getenv("EMAIL")
    app_password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart()

    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Smart Interview Practice System - OTP Verification"

    body = f"""
Hello,

Your OTP for Smart Interview Practice System is:

{otp}

This OTP is valid for 5 minutes.

Do not share this OTP with anyone.

Thank you.
"""

    message.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(sender_email, app_password)

    server.sendmail(
        sender_email,
        receiver_email,
        message.as_string()
    )

    server.quit()