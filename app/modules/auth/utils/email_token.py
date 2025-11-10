from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from dotenv import load_dotenv
import os

load_dotenv()

def generate_verification_token(email):
    s = URLSafeTimedSerializer(os.getenv("EMAIL_VERIFICATION_KEY"))
    return s.dumps(email, salt='email-confirm-salt')

def confirm_verification_token(token, expiration=3600):
    s = URLSafeTimedSerializer(os.getenv("EMAIL_VERIFICATION_KEY"))
    try:
        email = s.loads(token, salt='email-confirm-salt', max_age=expiration)
    except Exception:
        return None
    return email
