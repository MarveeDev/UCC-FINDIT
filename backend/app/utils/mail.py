import smtplib
import ssl
from email.mime.text import MIMEText

from flask import current_app


def send_otp_email(to_email, otp, purpose="email_verification"):
    """Send (or, in development, log) a verification code email.

    When no SMTP host is configured, the message is logged to the application
    logger so the authentication flow remains testable without a mail server.
    Real delivery requires SMTP_HOST to be configured.
    """
    app = current_app
    subject = "Your UCC FINDIT verification code"
    body = (
        f"Your UCC FINDIT verification code is {otp}.\n\n"
        f"This code expires in {app.config['OTP_EXPIRY_MINUTES']} minutes.\n"
        "If you did not request this code, you can safely ignore this email."
    )

    if app.config.get("MAIL_DEBUG", False):
        app.logger.info(
            "[DEV MAIL] to=%s subject=%s otp=%s purpose=%s",
            to_email,
            subject,
            otp,
            purpose,
        )

    if not app.config.get("SMTP_HOST"):
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
