from flask import redirect, render_template, request, session, url_for
from flask_login import current_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, RecoverPasswordForm, SendEmailForm, SignupForm, TwoFactoAuthForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")

        # Log user
        return render_template("auth/verify_email.html", email=user.email)

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        if authentication_service.check_password(form.email.data, form.password.data):
            if authentication_service.check_2FA_is_enabled(form.email.data):
                session["temp_mail"] = form.email.data
                session["temp_pass"] = form.password.data
                return redirect(url_for("auth.verify_2fa"))
            authentication_service.login(form.email.data, form.password.data)
            return redirect(url_for("public.index"))

        return render_template("auth/login_form.html", form=form, error="Invalid credentials")

    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))


@auth_bp.route("/enter_email", methods=["GET", "POST"])
def enter_email():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SendEmailForm()
    RecoverPasswordForm()

    if request.method == "POST" and form.validate_on_submit():
        user_email = form.email.data
        if not authentication_service.is_email_available(user_email):
            authentication_service.send_recover_email(user_email)
            return redirect(url_for("auth.change_password", email=user_email))
        else:
            return render_template("auth/send_email_for_recovery.html", form=form, error="Email doesnt exists")

    return render_template("auth/send_email_for_recovery.html", form=form)


@auth_bp.route("/change_password", methods=["GET", "POST"])
def change_password():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = RecoverPasswordForm()
    LoginForm()

    code = form.token.data
    password = form.password.data
    conf_password = form.confirm_password.data
    user_email = request.args.get("email")
    user = authentication_service.get_user_by_email(user_email)

    if form.validate_on_submit() and request.method == "POST":
        if authentication_service.validate_recovery(code, password, conf_password):
            authentication_service.update_password(user, password)
            return redirect(url_for("auth.login"))
        else:
            return render_template("auth/recover_password_form.html", form=form, error="something went wrong")

    return render_template("auth/recover_password_form.html", form=form)


@auth_bp.route("/enable_2fa", methods=["GET", "POST"])
def enable_2fa():
    if current_user.is_authenticated and current_user.twofa_key is None:
        if "temp_key" not in session:
            key, qr = authentication_service.generate_key_qr()
            session["temp_key"] = key
            session["temp_qr"] = qr

        key = session["temp_key"]
        qr = session["temp_qr"]

        form = TwoFactoAuthForm()
        if request.method == "POST" and form.validate_on_submit():
            if authentication_service.confirm_and_add_2fa(key, form.code.data):
                session.pop("temp_qr")
                session.pop("temp_key")
                return redirect(url_for("public.index"))
            return render_template("auth/tfa_verification.html", form=form, error="Incorrect 2FA code", qrcode=qr)

        return render_template("auth/tfa_verification.html", form=form, qrcode=qr)

    return redirect(url_for("auth.login"))


@auth_bp.route("/verify_2fa", methods=["GET", "POST"])
def verify_2fa():

    if session["temp_mail"] is None or session["temp_pass"] is None:
        return redirect(url_for("auth.login"))

    if current_user.is_anonymous:
        form = TwoFactoAuthForm()
        if request.method == "POST" and form.validate_on_submit():
            if authentication_service.validate_2fa_code(form.code.data, session["temp_mail"]):
                authentication_service.login(session["temp_mail"], session["temp_pass"])
                session.pop("temp_mail")
                session.pop("temp_pass")
                return redirect(url_for("public.index"))
            return render_template("auth/tfa_verification.html", form=form, error="Incorrect 2FA code")

        return render_template("auth/tfa_verification.html", form=form)

    return redirect(url_for("public.index"))


@auth_bp.route("/verify/<token>")
def verify_email(token):
    authentication_service.verify_email(token)
    return redirect(url_for("auth.login"))
