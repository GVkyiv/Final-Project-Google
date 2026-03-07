from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, List, Optional

DATE_FORMAT = "%d/%m/%Y"
LEGACY_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d.%m.%Y")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_date(raw: str) -> date:
    return datetime.strptime(raw, DATE_FORMAT).date()


def parse_date_flexible(raw: str) -> date:
    prepared = str(raw or "").strip()
    if not prepared:
        raise ValueError("Date value is empty.")

    for date_format in (DATE_FORMAT, *LEGACY_DATE_FORMATS):
        try:
            return datetime.strptime(prepared, date_format).date()
        except ValueError:
            pass

    # Legacy files may store ISO date or full ISO datetime.
    try:
        return datetime.fromisoformat(prepared).date()
    except ValueError:
        pass

    try:
        return datetime.fromisoformat(prepared.replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise ValueError(f"Unsupported date format: {prepared}") from exc


def format_date(value: date) -> str:
    return value.strftime(DATE_FORMAT)


def normalize_birthday(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    prepared = str(raw).strip()
    if not prepared:
        return None
    return format_date(parse_date_flexible(prepared))


def parse_iso_datetime(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


def normalize_name(name: str) -> str:
    return " ".join(name.strip().split()).lower()


def normalize_tags(raw_tags: Iterable[str]) -> List[str]:
    tags: List[str] = []
    for token in raw_tags:
        parts = [chunk.strip().lower() for chunk in str(token).split(",")]
        tags.extend([part for part in parts if part])
    return sorted(set(tags))


def split_csv(raw: str) -> List[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def to_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def text_or_none(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def ensure_list_of_strings(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return split_csv(value)
    return [str(value).strip()] if str(value).strip() else []


def next_birthday_date(birthday_raw: Optional[str], today: Optional[date] = None) -> Optional[date]:
    if not birthday_raw:
        return None
    base = parse_date_flexible(birthday_raw)
    current = today or date.today()
    year = current.year

    while True:
        try:
            candidate = base.replace(year=year)
        except ValueError:
            year += 1
            continue
        if candidate < current:
            year += 1
            continue
        return candidate
