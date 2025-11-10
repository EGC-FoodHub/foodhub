import os

from flask_login import current_user, login_user

from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.auth.twofa import generate_key, generate_qr, verify
from app.modules.auth.utils.email_helper import send_email_verification
from app.modules.auth.utils.email_token import confirm_verification_token, generate_verification_token
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService


class EmailVerificationError(Exception):
    """Raised when email verification fails."""


class AuthenticationService(BaseService):
    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()

    def login(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is None:
            return False

        if not user.check_password(password):
            return False

        if not user.is_email_verified:
            from flask import flash

            flash("Please verify your email before logging in.", "warning")
            return False

        login_user(user, remember=remember)
        return True

    def check_password(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            login_user(user, remember=remember)
            return True
        return False

    def check_password(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            return True
        return False

    def check_2FA_is_enabled(self, email):
        user: User | None = self.repository.get_by_email(email)
        if user is not None and user.twofa_key is not None:
            return True
        return False

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs):
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

    def generate_key_qr(self):
        if current_user.is_authenticated:
            key = generate_key()
            return key, generate_qr(key, current_user.profile.name)
        return None

    def confirm_and_add_2fa(self, encripted_key: str, code: str):
        if current_user.is_authenticated:
            comprobation = verify(encripted_key, code)
            if comprobation:
                # self.update(current_user.id, twofa_key=encripted_key)
                return True
        return False

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
