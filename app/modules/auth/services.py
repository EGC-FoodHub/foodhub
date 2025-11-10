import os
import resend
import secrets

from flask_login import current_user, login_user

from dotenv import load_dotenv

from app.modules.auth.models import User
from app.modules.auth.repositories import UserRepository
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

load_dotenv()

class AuthenticationService(BaseService):

    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()
        self.RESEND_API_KEY = os.getenv('RESEND_API_KEY')
        resend.api_key = self.RESEND_API_KEY

    def login(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            login_user(user, remember=remember)
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
            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
            self.repository.session.commit()
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

    def send_recover_email(self):
        resend.api_key = self.RESEND_API_KEY
        token = os.getenv('TOKEN_KEY',secrets.token_hex(6))

        params = {
            "from": "Acme <onboarding@resend.dev>",
            "to": ["miguelgvizcaino@gmail.com"],
            "subject": "FoodHub password change",
            "html": """
                <p>This is the your key for changing your password</p>
                <p><strong>{token}</strong></p>
                """.format(token=token)
        }

        email = resend.Emails.send(params)
        print(email)

    def validate_recovery_token(self, token):
        return token == os.getenv('TOKEN_KEY')

    def update_password(self, user_profile_id, new_password):
        self.update(user_profile_id,password = new_password)
        return None


if __name__ == "__main__":
    # código de prueba rápida
    servicio = AuthenticationService()

    servicio.send_recover_email()
    token1 = os.getenv('TOKEN_KEY')

    resultado = servicio.validate_recovery_token(token1)
    print("Resultado:", resultado)
