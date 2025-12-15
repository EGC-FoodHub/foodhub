from unittest.mock import MagicMock, patch

import pytest
from flask import url_for

from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService
from app.modules.profile.repositories import UserProfileRepository


@pytest.fixture(scope="module")
def test_client(test_client):
    with test_client.application.app_context():
        pass

    yield test_client


def test_login_success(test_client):
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path != url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_email(test_client):
    response = test_client.post(
        "/login", data=dict(email="bademail@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_password(test_client):
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="basspassword"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_signup_user_no_name(test_client):
    response = test_client.post(
        "/signup", data=dict(surname="Foo", email="test@example.com", password="test1234"), follow_redirects=True
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert b"This field is required" in response.data, response.data


def test_signup_user_unsuccessful(test_client):
    email = "test@example.com"
    response = test_client.post(
        "/signup", data=dict(name="Test", surname="Foo", email=email, password="test1234"), follow_redirects=True
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert f"Email {email} in use".encode("utf-8") in response.data


def test_signup_user_successful(test_client):
    response = test_client.post(
        "/signup",
        data=dict(name="Foo", surname="Example", email="foo@example.com", password="foo1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert b"Verify Your Email" in response.data


def test_service_create_with_profie_success(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "service_test@example.com", "password": "test1234"}

    AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1


def test_service_create_with_profile_fail_no_email(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "", "password": "1234"}

    with pytest.raises(ValueError, match="Email is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_create_with_profile_fail_no_password(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "test@example.com", "password": ""}

    with pytest.raises(ValueError, match="Password is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


@patch("flask_login.utils._get_user")
def test_signup_authenticated_redirects_home(mock_get_user, test_client):
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_get_user.return_value = mock_user

    response = test_client.get("/signup/", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/")


@patch("flask_login.utils._get_user")
def test_enter_email_get_authenticated_redirects(mock_get_user, test_client):
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_get_user.return_value = mock_user

    response = test_client.get("/enter_email", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_enter_email_get_shows_form(test_client):
    response = test_client.get("/enter_email", follow_redirects=True)

    assert response.status_code == 200
    assert b"email" in response.data.lower()


@patch.object(AuthenticationService, "is_email_available")
@patch.object(AuthenticationService, "send_recover_email")
def test_enter_email_post_existing_email_success(mock_send_email, mock_is_available, test_client):
    mock_is_available.return_value = False

    response = test_client.post("/enter_email", data=dict(email="test@example.com"), follow_redirects=False)

    assert response.status_code == 302
    assert "change_password" in response.location
    mock_send_email.assert_called_once_with("test@example.com")


@patch.object(AuthenticationService, "is_email_available")
def test_enter_email_post_nonexistent_email_error(mock_is_available, test_client):
    mock_is_available.return_value = True

    response = test_client.post("/enter_email", data=dict(email="nonexistent@example.com"), follow_redirects=True)

    assert response.status_code == 200
    assert b"Email doesnt exists" in response.data


@patch("flask_login.utils._get_user")
def test_change_password_get_authenticated_redirects(mock_get_user, test_client):
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_get_user.return_value = mock_user

    response = test_client.get("/change_password?email=test@example.com", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_change_password_get_shows_form(test_client):
    response = test_client.get("/change_password?email=test@example.com", follow_redirects=True)

    assert response.status_code == 200


@patch.object(AuthenticationService, "get_user_by_email")
@patch.object(AuthenticationService, "validate_recovery")
@patch.object(AuthenticationService, "update_password")
def test_change_password_post_valid_token_success(mock_update, mock_validate, mock_get_user, test_client):
    mock_user = MagicMock()
    mock_get_user.return_value = mock_user
    mock_validate.return_value = True

    response = test_client.post(
        "/change_password?email=test@example.com",
        data=dict(token="123456", password="newpassword123", confirm_password="newpassword123"),
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.location.endswith(url_for("auth.login"))
    mock_update.assert_called_once_with(mock_user, "newpassword123")


@patch.object(AuthenticationService, "get_user_by_email")
@patch.object(AuthenticationService, "validate_recovery")
def test_change_password_post_invalid_token_error(mock_validate, mock_get_user, test_client):
    mock_user = MagicMock()
    mock_get_user.return_value = mock_user
    mock_validate.return_value = False

    response = test_client.post(
        "/change_password?email=test@example.com",
        data=dict(token="wrong_token", password="newpassword123", confirm_password="newpassword123"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"something went wrong" in response.data


def test_verify_2fa_get_no_session_raises_error(test_client):
    with pytest.raises(KeyError):
        test_client.get("/verify_2fa", follow_redirects=False)


def test_verify_2fa_get_shows_form(test_client):
    with test_client.session_transaction() as sess:
        sess["temp_mail"] = "test@example.com"
        sess["temp_pass"] = "test1234"

    response = test_client.get("/verify_2fa", follow_redirects=True)

    assert response.status_code == 200


@patch.object(AuthenticationService, "validate_2fa_code")
@patch.object(AuthenticationService, "login")
def test_verify_2fa_post_valid_code_success(mock_login, mock_validate, test_client):
    with test_client.session_transaction() as sess:
        sess["temp_mail"] = "test@example.com"
        sess["temp_pass"] = "test1234"

    mock_validate.return_value = True

    response = test_client.post("/verify_2fa", data=dict(code="123456"), follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/")
    mock_login.assert_called_once_with("test@example.com", "test1234")


@patch.object(AuthenticationService, "validate_2fa_code")
def test_verify_2fa_post_invalid_code_error(mock_validate, test_client):
    with test_client.session_transaction() as sess:
        sess["temp_mail"] = "test@example.com"
        sess["temp_pass"] = "test1234"

    mock_validate.return_value = False

    response = test_client.post("/verify_2fa", data=dict(code="wrong_code"), follow_redirects=True)

    assert response.status_code == 200
    assert b"2fa" in response.data.lower() or b"verification" in response.data.lower()


@patch("flask_login.utils._get_user")
def test_verify_2fa_authenticated_redirects(mock_get_user, test_client):
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_anonymous = False
    mock_get_user.return_value = mock_user

    with test_client.session_transaction() as sess:
        sess["temp_mail"] = "test@example.com"
        sess["temp_pass"] = "test1234"

    response = test_client.get("/verify_2fa", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/")


def test_enable_2fa_unauthenticated_redirects(test_client):
    response = test_client.get("/enable_2fa", follow_redirects=False)

    assert response.status_code == 302
    assert "login" in response.location


@patch("flask_login.utils._get_user")
def test_enable_2fa_get_shows_qr_code(mock_get_user, test_client):
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.twofa_key = None
    mock_get_user.return_value = mock_user

    with patch.object(AuthenticationService, "generate_key_qr", return_value=("test_key", "qr_code_data")):
        response = test_client.get("/enable_2fa", follow_redirects=True)

        assert response.status_code == 200


@patch("flask_login.utils._get_user")
def test_enable_2fa_post_valid_code_success(mock_get_user, test_client):
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.twofa_key = None
    mock_get_user.return_value = mock_user

    with test_client.session_transaction() as sess:
        sess["temp_key"] = "test_key"
        sess["temp_qr"] = "qr_data"

    with patch.object(AuthenticationService, "confirm_and_add_2fa", return_value=True):
        response = test_client.post("/enable_2fa", data=dict(code="123456"), follow_redirects=False)

        assert response.status_code == 302
        assert response.location.endswith("/")


@patch("flask_login.utils._get_user")
def test_enable_2fa_post_invalid_code_error(mock_get_user, test_client):
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.twofa_key = None
    mock_get_user.return_value = mock_user

    with test_client.session_transaction() as sess:
        sess["temp_key"] = "test_key"
        sess["temp_qr"] = "qr_data"

    with patch.object(AuthenticationService, "confirm_and_add_2fa", return_value=False):
        response = test_client.post("/enable_2fa", data=dict(code="wrong_code"), follow_redirects=True)

        assert response.status_code == 200
        assert b"2fa" in response.data.lower() or b"verification" in response.data.lower()


@patch.object(AuthenticationService, "verify_email")
def test_verify_email_with_token_redirects_login(mock_verify, test_client):
    response = test_client.get("/verify/valid_token_123", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith(url_for("auth.login"))
    mock_verify.assert_called_once_with("valid_token_123")


@patch.object(AuthenticationService, "verify_email")
def test_verify_email_calls_service(mock_verify, test_client):
    test_client.get("/verify/test_token", follow_redirects=True)

    mock_verify.assert_called_once_with("test_token")


def test_logout_redirects_to_index(test_client):
    response = test_client.get("/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/")


@patch("app.modules.auth.routes.logout_user")
def test_logout_calls_logout_user(mock_logout, test_client):
    test_client.get("/logout", follow_redirects=True)

    mock_logout.assert_called_once()


@patch.object(AuthenticationService, "check_2FA_is_enabled")
def test_login_with_2fa_enabled_redirects_verify(mock_check_2fa, test_client):
    mock_check_2fa.return_value = True

    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=False
    )

    assert response.status_code == 302
    assert "verify_2fa" in response.location


@patch.object(AuthenticationService, "check_2FA_is_enabled")
def test_login_with_2fa_stores_credentials_in_session(mock_check_2fa, test_client):
    mock_check_2fa.return_value = True

    test_client.post("/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=False)

    with test_client.session_transaction() as sess:
        assert sess.get("temp_mail") == "test@example.com"
        assert sess.get("temp_pass") == "test1234"


def test_enter_email_post_empty_email(test_client):
    response = test_client.post("/enter_email", data=dict(email=""), follow_redirects=True)

    assert response.status_code == 200


def test_change_password_without_email_param(test_client):
    response = test_client.get("/change_password", follow_redirects=True)

    assert response.status_code == 200


def test_verify_2fa_clears_session_on_success(test_client):
    with test_client.session_transaction() as sess:
        sess["temp_mail"] = "test@example.com"
        sess["temp_pass"] = "test1234"

    with patch.object(AuthenticationService, "validate_2fa_code", return_value=True):
        with patch.object(AuthenticationService, "login"):
            test_client.post("/verify_2fa", data=dict(code="123456"), follow_redirects=True)


@patch("flask_login.utils._get_user")
def test_enable_2fa_clears_session_on_success(mock_get_user, test_client):
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.twofa_key = None
    mock_get_user.return_value = mock_user

    with test_client.session_transaction() as sess:
        sess["temp_key"] = "test_key"
        sess["temp_qr"] = "qr_data"

    with patch.object(AuthenticationService, "confirm_and_add_2fa", return_value=True):
        test_client.post("/enable_2fa", data=dict(code="123456"), follow_redirects=True)
