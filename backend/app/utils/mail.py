import smtplib
import ssl
from email.mime.text import MIMEText

from flask import current_app


def send_otp_email(to_email, otp, purpose="email_verification"):
    """Send (or, in development, log) a verification code email.

    In development (MAIL_DEBUG), the code is logged to the application logger so
    the authentication flow remains testable without a mail server. In
    production, a missing SMTP host is an explicit configuration error rather
    than a silent loss of the verification email.
    """
    app = current_app
    subject = "Your UCC FINDIT verification code"
    body = (
        f"Your UCC FINDIT verification code is {otp}.\n\n"
        f"This code expires in {app.config['OTP_EXPIRY_MINUTES']} minutes.\n"
        "If you did not request this code, you can safely ignore this email."
    )

    mail_debug = app.config.get("MAIL_DEBUG", False)
    if mail_debug:
        app.logger.info(
            "[DEV MAIL] to=%s subject=%s otp=%s purpose=%s",
            to_email,
            subject,
            otp,
            purpose,
        )

    if not app.config.get("SMTP_HOST"):
        if not mail_debug:
            raise RuntimeError(
                "Email delivery is not configured (SMTP_HOST is missing)"
            )
        return

    _send_smtp(to_email, subject, body)


def _send_smtp(to_email, subject, body):
    app = current_app
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = app.config.get("MAIL_FROM")
    message["To"] = to_email

    context = ssl.create_default_context()
    with smtplib.SMTP(app.config.get("SMTP_HOST"), app.config.get("SMTP_PORT", 587), timeout=15) as server:
        server.starttls(context=context)
        if app.config.get("SMTP_USER"):
            server.login(app.config.get("SMTP_USER"), app.config.get("SMTP_PASSWORD"))
        server.sendmail(message["From"], [to_email], message.as_string())
