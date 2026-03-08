from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Tuple

from .utils import ensure_list_of_strings, normalize_birthday, normalize_tags, now_iso, text_or_none, to_bool


def _split_legacy_phone(raw_phone: str) -> Tuple[str, str]:
    """Helper for reading legacy files."""
    prepared = str(raw_phone or "").strip()
    if not prepared:
        return "", ""

    match = re.match(r"^(\+\d{1,4})(?:[\s\-]+)?(.*)$", prepared)
    if match:
        code = match.group(1).strip()
        number_raw = match.group(2).strip()
    else:
        code = ""
        number_raw = prepared

    normalized_number = re.sub(r"[^0-9]", "", number_raw)
    return code, normalized_number


def _compose_phone(code: str, number: str) -> str:
    """Helper for reading legacy files."""
    prepared_code = str(code or "").strip()
    prepared_number = re.sub(r"[^0-9]", "", str(number or ""))
    if prepared_code and prepared_number:
        return f"{prepared_code} {prepared_number}"
    return prepared_code or prepared_number


def _safe_positive_int(value: object, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


@dataclass
class Contact:
    id: int
    first_name: str
    last_name: str = ""
    country: str = ""
    phone_number: str = ""
    email: str | None = None
    address: str | None = None
    birthday: str | None = None
    comment: str = ""
    favorite: bool = False
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def __post_init__(self):
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        self.country = self.country.strip()
        self.phone_number = self.phone_number.strip()
        if self.email:
            self.email = self.email.strip()
        if self.address:
            self.address = self.address.strip()
        if self.birthday:
            self.birthday = self.birthday.strip()

    @property
    def display_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(part for part in parts if part)

    @property
    def formatted_phone(self) -> str:
        return self.phone_number

    # Legacy compatibility, mainly for CLI code reading older Contact formats
    @property
    def name(self) -> str:
        return self.display_name or self.first_name

    @classmethod
    def from_dict(cls, raw: Dict[str, object], fallback_id: int) -> "Contact":
        created_at = text_or_none(raw.get("created_at")) or now_iso()

        first_name = text_or_none(raw.get("first_name"))
        if not first_name:
            first_name = text_or_none(raw.get("name")) or f"Contact {fallback_id}"

        # Legacy compatibility: old records may contain nickname, but GUI/model no longer use it.
        _ = text_or_none(raw.get("nickname"))

        last_name = text_or_none(raw.get("last_name")) or ""
        country = text_or_none(raw.get("country")) or ""
        phone_number = text_or_none(raw.get("phone_number")) or ""
        legacy_code = text_or_none(raw.get("country_phone_code")) or ""

        if not phone_number:
            legacy_phones = ensure_list_of_strings(raw.get("phones"))
            legacy_single_phone = text_or_none(raw.get("phone"))
            if legacy_single_phone:
                legacy_phones.append(legacy_single_phone)

            if legacy_phones:
                code, number = _split_legacy_phone(legacy_phones[0])
                phone_number = _compose_phone(code, number)
        else:
            if phone_number.startswith("+"):
                code, number = _split_legacy_phone(phone_number)
                phone_number = _compose_phone(code, number)
            elif legacy_code:
                phone_number = _compose_phone(legacy_code, phone_number)
            else:
                phone_number = re.sub(r"[^0-9]", "", phone_number)

        birthday_raw = text_or_none(raw.get("birthday"))
        try:
            birthday = normalize_birthday(birthday_raw)
        except ValueError:
            birthday = None

        return cls(
            id=_safe_positive_int(raw.get("id"), fallback_id),
            first_name=first_name,
            last_name=last_name,
            country=country,
            phone_number=phone_number,
            email=text_or_none(raw.get("email")),
            address=text_or_none(raw.get("address")),
            birthday=birthday,
            comment=str(raw.get("comment") or "").strip(),
            favorite=to_bool(raw.get("favorite"), default=False),
            created_at=created_at,
            updated_at=text_or_none(raw.get("updated_at")) or created_at,
        )

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class Note:
    id: int
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    pinned: bool = False
    favorite: bool = False
    color_label: str = "default"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def __post_init__(self):
        self.title = self.title.strip()
        self.content = self.content.strip()

    @classmethod
    def from_dict(cls, raw: Dict[str, object], fallback_id: int) -> "Note":
        note_id = _safe_positive_int(raw.get("id") or raw.get("note_id"), fallback_id)
        content = str(raw.get("content") or raw.get("text") or "").strip()
        title = str(raw.get("title") or "").strip()
        if not title:
            title = content.splitlines()[0][:40] if content else f"Note {note_id}"

        created_at = text_or_none(raw.get("created_at")) or now_iso()
        return cls(
            id=note_id,
            title=title,
            content=content,
            tags=normalize_tags(ensure_list_of_strings(raw.get("tags"))),
            pinned=to_bool(raw.get("pinned"), default=False),
            favorite=to_bool(raw.get("favorite"), default=False),
            color_label=str(raw.get("color_label") or "default"),
            created_at=created_at,
            updated_at=text_or_none(raw.get("updated_at")) or created_at,
        )

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class AppSettings:
    language: str = "en"
    ui_density: str = "normal"
    appearance_mode: str = "system"
    data_path: str | None = None

    @classmethod
    def from_raw(cls, raw: Dict[str, object]) -> "AppSettings":
        language = str(raw.get("language") or "en")
        if language not in {"en", "uk"}:
            language = "en"

        density = str(raw.get("ui_density") or "normal")
        if density not in {"compact", "normal"}:
            density = "normal"

        appearance_mode = str(raw.get("appearance_mode") or "system")
        if appearance_mode not in {"light", "dark", "system"}:
            appearance_mode = "system"

        data_path_value = text_or_none(raw.get("data_path"))
        return cls(
            language=language,
            ui_density=density,
            appearance_mode=appearance_mode,
            data_path=data_path_value,
        )

    def to_raw(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class AppData:
    contacts: List[Contact] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)
    next_contact_id: int = 1
    next_note_id: int = 1

    @classmethod
    def from_raw(cls, raw: Dict[str, object]) -> "AppData":
        raw_contacts = raw.get("contacts", [])
        raw_notes = raw.get("notes", [])

        if isinstance(raw_contacts, dict):
            raw_contacts = list(raw_contacts.values())
        if isinstance(raw_notes, dict):
            raw_notes = list(raw_notes.values())

        contacts: List[Contact] = []
        used_contact_ids: set[int] = set()
        for idx, entry in enumerate(raw_contacts, start=1):
            if not isinstance(entry, dict):
                continue
            contact = Contact.from_dict(entry, fallback_id=idx)
            candidate = contact.id
            if candidate in used_contact_ids or candidate <= 0:
                candidate = max(used_contact_ids, default=0) + 1
            contact.id = candidate
            used_contact_ids.add(candidate)
            contacts.append(contact)

        notes: List[Note] = []
        used_note_ids: set[int] = set()
        for idx, entry in enumerate(raw_notes, start=1):
            if not isinstance(entry, dict):
                continue
            note = Note.from_dict(entry, fallback_id=idx)
            candidate = note.id
            if candidate in used_note_ids or candidate <= 0:
                candidate = max(used_note_ids, default=0) + 1
            note.id = candidate
            used_note_ids.add(candidate)
            notes.append(note)

        max_contact_id = max((contact.id for contact in contacts), default=0)
        max_note_id = max((note.id for note in notes), default=0)

        next_contact_id = _safe_positive_int(raw.get("next_contact_id"), max_contact_id + 1)
        next_note_id = _safe_positive_int(raw.get("next_note_id"), max_note_id + 1)

        return cls(
            contacts=contacts,
            notes=notes,
            next_contact_id=max(next_contact_id, max_contact_id + 1),
            next_note_id=max(next_note_id, max_note_id + 1),
        )

    def to_raw(self) -> Dict[str, object]:
        return {
            "schema_version": 3,
            "contacts": [
                contact.to_dict()
                for contact in sorted(
                    self.contacts,
                    key=lambda item: (
                        item.first_name.lower(),
                        item.last_name.lower(),
                        item.id,
                    ),
                )
            ],
            "notes": [note.to_dict() for note in sorted(self.notes, key=lambda item: item.id)],
            "next_contact_id": self.next_contact_id,
            "next_note_id": self.next_note_id,
        }

