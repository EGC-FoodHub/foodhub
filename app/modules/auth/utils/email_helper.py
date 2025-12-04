import os
from dotenv import load_dotenv
import requests

from app.modules.auth.models import User

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = os.getenv("SENDER_NAME", "FoodHub")
BASE_URL = os.getenv("DOMAIN")


def send_email_verification(user: User):
    if not BREVO_API_KEY:
        print("Error: BREVO_API_KEY no está configurada")
        return False

    if not SENDER_EMAIL:
        print("Error: SENDER_EMAIL no está configurada")
        return False

    verification_link = f"{BASE_URL}/verify/{user.email_verification_token}"

    html_template = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8" />
        <title>FoodHub - Verify Your Account</title>
      </head>
      <body style="font-family: Arial, sans-serif; background-color: #f6f8fa; padding: 40px;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 12px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-top: 6px solid #0366d6;">
          <h2 style="text-align:center; color:#0366d6; margin-bottom: 20px; font-weight: 600;">
            Welcome to FoodHub, {user.profile.name} {user.profile.surname}! 🍽️
          </h2>

          <p style="color:#444; font-size: 16px; line-height: 1.6;">
            Hi {user.profile.name}, please confirm your email address to complete your signup.
          </p>

          <div style="text-align:center; margin: 32px 0;">
            <a href="{verification_link}"
               style="background:#0366d6; color:white; padding:14px 28px; text-decoration:none; font-size:16px;
                      border-radius:8px; display:inline-block; font-weight:600;">
              Verify My Email
            </a>
          </div>

          <p style="color:#555; font-size:15px; line-height:1.6; text-align:center;">
            If the button above doesn’t work, copy and paste this link into your browser:<br>
            <a href="{verification_link}" style="color:#0366d6; word-break: break-all;">{verification_link}</a>
          </p>

          <hr style="border: none; border-top: 1px solid #e1e4e8; margin: 30px 0;">

          <p style="color:#777; text-align:center; font-size:12px; line-height:1.5;">
            If you didn’t sign up for FoodHub, you can safely ignore this email.
          </p>
        </div>
      </body>
    </html>
    """

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    data = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": user.email}],
        "subject": "Verify your FoodHub account",
        "htmlContent": html_template
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print(f"Verification email sent to {user.email}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending verification email: {e}")
