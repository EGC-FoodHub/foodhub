import pyotp
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import qrcode
import base64
import io

load_dotenv()

def generate_key():
    cipher = Fernet(os.getenv("MASTER_KEY").encode())
    key = pyotp.random_base32()
    cifrado = cipher.encrypt(key.encode())
    return cifrado

def decript_key(key: str | bytes):
    cipher = Fernet(os.getenv("MASTER_KEY").encode())
    raw_key = cipher.decrypt(key)
    
    return raw_key.decode("utf-8")


def verify(encripted_key:str, code: int):
    key = decript_key(encripted_key)
    totp = pyotp.TOTP(key)
    return totp.verify(code)

def generate_qr(encripted_key: str, username: str):
    key = decript_key(encripted_key)
    uri = pyotp.totp.TOTP(key).provisioning_uri(name=username,issuer_name="Foodhub")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf,format="PNG")
    qrname = f'{username}_qrcode.png'
    img_base64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return img_base64

