"""Resend email delivery service.

Sends branded UCC FINDIT verification emails through the Resend HTTP API.
This module never logs the plaintext OTP; only the recipient address is
included in log output.
"""

import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailDeliveryError(Exception):
    """Raised when a verification email cannot be delivered via Resend."""


def send_otp_email(to_email, otp):
    """Deliver a UCC FINDIT verification code email via the Resend API.

    Raises EmailDeliveryError when the API key/sender is missing or the Resend
    API rejects/does not reach the request. The plaintext OTP is included only
    in the outgoing email payload and never written to logs.
    """
    app = current_app
    api_key = app.config.get("RESEND_API_KEY")
    mail_from = app.config.get("MAIL_FROM")
    if not api_key or not mail_from:
        raise EmailDeliveryError("Email delivery is not configured")

    expiry_minutes = app.config["OTP_EXPIRY_MINUTES"]
    html, text = _render_verification_email(otp, expiry_minutes)

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": mail_from,
                "to": [to_email],
                "subject": "Your UCC FINDIT verification code",
                "html": html,
                "text": text,
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        logger.error(
            "Resend email delivery failed (%s)", type(exc).__name__
        )
        raise EmailDeliveryError("Email delivery failed") from exc

    if response.status_code >= 400:
        logger.error("Resend rejected email with status %s", response.status_code)
        raise EmailDeliveryError("Email delivery failed")

    logger.info("Verification email sent to %s", to_email)


def _render_verification_email(otp, expiry_minutes):
    """Return (html, text) for a branded UCC FINDIT verification email."""
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5174")
    verify_url = f"{frontend_url.rstrip('/')}/verify-email"

    text = (
        "UCC FINDIT\n\n"
        f"Your verification code is: {otp}\n\n"
        f"This code expires in {expiry_minutes} minutes.\n"
        "If you did not request this code, you can safely ignore this email.\n\n"
        f"Verify your email: {verify_url}\n"
    )

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin:0;padding:0;background-color:#f0fdf4;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0fdf4;padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background-color:#ffffff;border-radius:12px;padding:32px;">
          <tr>
            <td>
              <p style="font-family:Georgia,serif;font-size:26px;font-weight:bold;color:#064e3b;margin:0 0 8px;">UCC FINDIT</p>
              <p style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#334155;margin:0 0 24px;">Use the code below to verify your email address and finish creating your account.</p>
              <div style="font-family:'Courier New',monospace;font-size:32px;font-weight:bold;letter-spacing:8px;color:#065f46;background-color:#ecfdf5;border:1px dashed #10b981;border-radius:8px;padding:16px;text-align:center;margin:0 0 16px;">{otp}</div>
              <p style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#64748b;margin:0 0 24px;">This code expires in {expiry_minutes} minutes. If you did not request this code, you can safely ignore this email.</p>
              <a href="{verify_url}" style="display:inline-block;background-color:#10b981;color:#ffffff;font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:bold;text-decoration:none;padding:12px 24px;border-radius:8px;">Verify my email</a>
              <p style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#94a3b8;margin:24px 0 0;">UCC FINDIT &middot; Campus Lost &amp; Found</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return html, text
