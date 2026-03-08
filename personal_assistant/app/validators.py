from __future__ import annotations

import re

from .exceptions import ValidationError
from .utils import DATE_FORMAT, parse_date

LEGACY_PHONE_PATTERN = re.compile(r"^\+?[0-9\-\s\(\)]{7,20}$")
PHONE_CODE_PATTERN = re.compile(r"^\+\d{1,4}$")
PHONE_NUMBER_ALLOWED_PATTERN = re.compile(r"^[0-9\-\s\(\)]{5,20}$")
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
BIRTHDAY_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def validate_required(value: str, field_name: str) -> str:
    prepared = value.strip()
    if not prepared:
        raise ValidationError(f"{field_name} is required.")
    return prepared


def validate_country_phone_code(code: str) -> str:
    prepared = code.strip()
    if not PHONE_CODE_PATTERN.fullmatch(prepared):
        raise ValidationError("Invalid country phone code. Use format +123.")
    return prepared


def validate_phone_number(phone_number: str) -> str:
    prepared = phone_number.strip()
    if not PHONE_NUMBER_ALLOWED_PATTERN.fullmatch(prepared):
        raise ValidationError("Invalid phone number. Use digits, spaces, parentheses or hyphen.")

    normalized = re.sub(r"[\s\-\(\)]", "", prepared)
    if not normalized.isdigit():
        raise ValidationError("Invalid phone number. Use digits only in the number part.")

    if len(normalized) < 5 or len(normalized) > 15:
        raise ValidationError("Phone number should contain from 5 to 15 digits.")

    return normalized


def validate_phone(phone: str) -> str:
    """Legacy validator kept for CLI compatibility with --phone values."""
    prepared = phone.strip()
    if not LEGACY_PHONE_PATTERN.fullmatch(prepared):
        raise ValidationError(f"Invalid phone number: {phone}")

    if prepared.startswith("+"):
        parts = prepared.split(maxsplit=1)
        code = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        if PHONE_CODE_PATTERN.fullmatch(code):
            if rest:
                return f"{validate_country_phone_code(code)} {validate_phone_number(rest)}"
            return validate_country_phone_code(code)

        # Keep accepting old format like +353871234567 for backward compatibility.
        if re.fullmatch(r"^\+\d{6,19}$", prepared):
            return prepared

    return validate_phone_number(prepared)


def validate_email(email: str) -> str:
    prepared = email.strip()
    if not EMAIL_PATTERN.fullmatch(prepared):
        raise ValidationError(f"Invalid email: {email}")
    return prepared


def validate_birthday(birthday: str) -> str:
    prepared = birthday.strip()
    if not BIRTHDAY_PATTERN.fullmatch(prepared):
        raise ValidationError(f"Invalid birthday format: {birthday}. Use {DATE_FORMAT}.")

    try:
        parse_date(prepared)
    except ValueError as exc:
        raise ValidationError(f"Invalid birthday value: {birthday}. Use {DATE_FORMAT}.") from exc

    return prepared

