import re

from email_validator import EmailNotValidError, validate_email
from flask import current_app


def normalize_email(email):
    """Return a normalized lowercase email, or None when invalid."""
    try:
        info = validate_email(email, check_deliverability=False)
        return info.normalized.lower()
    except EmailNotValidError:
        return None


def email_domain_allowed(email):
    """Return True when the email domain is in the configured UCC domain list."""
    domains = current_app.config.get("UCC_EMAIL_DOMAINS", [])
    if not domains:
        return True
    _, _, domain = email.rpartition("@")
    return domain.lower() in {d.lower() for d in domains}


def validate_password(password):
    """Return an error message when the password is too weak, else None."""
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if not re.search(r"[A-Za-z]", password):
        return "Password must contain at least one letter"
    if not re.search(r"\d", password):
        return "Password must contain at least one number"
    return None


def validate_registration(data):
    errors = {}
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    raw_email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not first_name:
        errors["first_name"] = "First name is required"
    elif len(first_name) > 80:
        errors["first_name"] = "First name is too long"

    if not last_name:
        errors["last_name"] = "Last name is required"
    elif len(last_name) > 80:
        errors["last_name"] = "Last name is too long"

    email = normalize_email(raw_email)
    if not email:
        errors["email"] = "A valid email address is required"
    elif current_app.config.get("ENFORCE_UCC_DOMAIN") and not email_domain_allowed(email):
        errors["email"] = "Please use your official UCC email address"

    password_error = validate_password(password)
    if password_error:
        errors["password"] = password_error

    return errors, first_name, last_name, email, password
