import os
import secrets

import resend
from dotenv import load_dotenv
from flask_login import current_user, login_user

from app import db
from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.auth.twofa import generate_key, generate_qr, verify
from app.modules.auth.utils.email_helper import send_email_verification
from app.modules.auth.utils.email_token import confirm_verification_token, generate_verification_token
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

load_dotenv()


class EmailVerificationError(Exception):
    """Raised when email verification fails."""


class AuthenticationService(BaseService):

    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()
        self.RESEND_API_KEY = os.getenv("RESEND_API_KEY")
        resend.api_key = self.RESEND_API_KEY

    def login(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is None:
            return False

        if not user.check_password(password):
            return False

        if not user.is_email_verified:
            return False

        login_user(user, remember=remember)
        return True

    def check_password(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            return True
        return False

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs) -> User | None:
        try:
            email = kwargs.pop("email", None)
            password = kwargs.pop("password", None)
            name = kwargs.pop("name", None)
            surname = kwargs.pop("surname", None)

            if not email:
                raise ValueError("Email is required.")
            if not password:
                raise ValueError("Password is required.")
            if not name:
                raise ValueError("Name is required.")
            if not surname:
                raise ValueError("Surname is required.")

            user_data = {"email": email, "password": password}

            profile_data = {
                "name": name,
                "surname": surname,
            }

            user = self.create(commit=False, **user_data)

            token = generate_verification_token(email)
            user.email_verification_token = token

            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
            self.repository.session.commit()

            send_email_verification(user)

        except Exception as exc:
            self.repository.session.rollback()
            raise exc
        return user

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None

        return None, form.errors

    def get_authenticated_user(self) -> User | None:
        if current_user.is_authenticated:
            return current_user
        return None

    def get_authenticated_user_profile(self) -> UserProfile | None:
        if current_user.is_authenticated:
            return current_user.profile
        return None

    def temp_folder_by_user(self, user: User) -> str:
        return os.path.join(uploads_folder_name(), "temp", str(user.id))

    def get_user_by_email(self, email) -> User | None:
        print(email)
        if not self.is_email_available(email):
            return self.repository.get_by_email(email)
        return None

    def send_recover_email(self, email):
        resend.api_key = self.RESEND_API_KEY
        token = secrets.token_hex(6)

        os.environ["TOKEN_KEY"] = token

        params = {
            "from": "Acme <onboarding@resend.dev>",
            "to": [email],
            "subject": "FoodHub password change",
            "html": """
                <p>This is the your key for changing your password</p>
                <p><strong>{token}</strong></p>
                """.format(
                token=token
            ),
        }

        email = resend.Emails.send(params)

    def validate_recovery(self, token, new_password, confirm_password):
        return token == os.getenv("TOKEN_KEY") and new_password == confirm_password

    def update_password(self, user, new_password):
        user.set_password(new_password)
        db.session.commit()

    def check_2FA_is_enabled(self, email):
        user: User | None = self.repository.get_by_email(email)
        if user is not None and getattr(user, "twofa_key", None) is not None:
            return True
        return False

    def generate_key_qr(self):
        if current_user.is_authenticated:
            key = generate_key()
            return key, generate_qr(key, current_user.profile.name)
        return None

    def confirm_and_add_2fa(self, encripted_key: str, code: str):
        if current_user.is_authenticated:
            comprobation = verify(encripted_key, code)
            if comprobation:
                self.update(current_user.id, twofa_key=encripted_key)
                return True
        return False

    def validate_2fa_code(self, code: int, email=None):

        if getattr(current_user, "is_authenticated", None):
            user = current_user
        elif email is not None:
            user = self.repository.get_by_email(email)
        else:
            return False

        comprobation = verify(user.twofa_key, code)
        return comprobation

    def verify_email(self, token: str):
        email = confirm_verification_token(token)
        if not email:
            raise EmailVerificationError("Invalid or expired verification token.")

        user = self.repository.get_by_email(email)
        if not user:
            raise EmailVerificationError("User not found for the given token.")

        if user.is_email_verified:
            raise EmailVerificationError("Email already verified.")

        user.is_email_verified = True
        user.email_verification_token = None
        self.repository.session.commit()

        return user
