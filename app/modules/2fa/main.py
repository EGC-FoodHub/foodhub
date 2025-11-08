import pyotp
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import qrcode

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


def verify(key:str, code: int):
    totp = pyotp.TOTP(key)
    print(totp.verify(code))

def generate_qr(key: str, username: str):
    uri = pyotp.totp.TOTP(key).provisioning_uri(name=username,issuer_name="Foodhub")
    img = qrcode.make(uri)
    qrname = f'{username}_qrcode.png'
    img.save(f"./app/static/img/qrcode/{qrname}")


generate_qr(decript_key(generate_key()),"Juan")

generate_qr(decript_key(generate_key()),"Emilio")