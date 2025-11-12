import os

import resend
from dotenv import load_dotenv

from app.modules.auth.models import User

load_dotenv()


def send_email_verification(user: User):
    # Set your API key (get it from https://resend.com/api-keys)
    resend.api_key = os.getenv("RESEND_API_KEY")
    base_url = "localhost:5000"
    verification_link = f"{base_url}/verify/{user.email_verification_token}"
    params = {
        "from": "onboarding@resend.dev",
        "to": [user.email],
        "subject": "Verify your FoodHub account",
        "html": f"""
  <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial,
   sans-serif; color: #333; max-width: 600px; margin: auto; padding: 20px;
    border: 1px solid #e1e4e8; border-radius: 8px; background-color: #f6f8fa;">
      <h2 style="color: #0366d6;">Welcome to FoodHub, {user.profile.name} {user.profile.surname}! 🍽️</h2>
      <p>Hi {user.profile.name}, please confirm your email address to complete your signup.</p>

      <p style="text-align: center; margin: 30px 0;">
          <a href="{verification_link}"
            style="background-color: #0366d6; color: white; padding: 12px 24px;
                text-decoration: none; border-radius: 6px; display: inline-block; font-weight: 600;">
              Verify My Email
          </a>
      </p>

      <p style="text-align: center; font-size: 14px; color: #555;">
          If the button above doesn’t work, copy and paste this link into your browser:
          <br>
          <a href="{verification_link}" style="color: #0366d6; word-break: break-all;">{verification_link}</a>
      </p>

      <hr style="border: none; border-top: 1px solid #e1e4e8; margin: 30px 0;">

      <p style="font-size: 12px; color: #888;">If you didn’t sign up for FoodHub, you can safely ignore this email.</p>
  </div>
  """,
    }

    # Send the email
    resend.Emails.send(params)
