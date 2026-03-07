from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import AppData, Contact, Note
from .storage import JsonStorage
from .utils import format_date, next_birthday_date, normalize_name, normalize_tags, now_iso, parse_date_flexible
from .validators import (
    validate_birthday,
    validate_email,
    validate_phone,
    validate_phone_number,
    validate_required,
)

COUNTRY_PHONE_CODES: Dict[str, str] = {
    "Ireland": "+353",
    "Ukraine": "+380",
    "Poland": "+48",
    "Germany": "+49",
    "United Kingdom": "+44",
    "Austria": "+43",
    "Switzerland": "+41",
    "France": "+33",
    "Spain": "+34",
    "Italy": "+39",
    "United States": "+1",
    "Canada": "+1",
    "Netherlands": "+31",
    "Belgium": "+32",
    "Portugal": "+351",
    "Sweden": "+46",
    "Norway": "+47",
    "Denmark": "+45",
    "Finland": "+358",
    "Czech Republic": "+420",
    "Slovakia": "+421",
    "Romania": "+40",
    "Hungary": "+36",
}

COUNTRY_LOCALIZED_NAMES: Dict[str, Dict[str, str]] = {
    "Ireland": {"en": "Ireland", "uk": "Ірландія"},
    "Ukraine": {"en": "Ukraine", "uk": "Україна"},
    "Poland": {"en": "Poland", "uk": "Польща"},
    "Germany": {"en": "Germany", "uk": "Німеччина"},
    "United Kingdom": {"en": "United Kingdom", "uk": "Велика Британія"},
    "Austria": {"en": "Austria", "uk": "Австрія"},
    "Switzerland": {"en": "Switzerland", "uk": "Швейцарія"},
    "France": {"en": "France", "uk": "Франція"},
    "Spain": {"en": "Spain", "uk": "Іспанія"},
    "Italy": {"en": "Italy", "uk": "Італія"},
    "United States": {"en": "United States", "uk": "США"},
    "Canada": {"en": "Canada", "uk": "Канада"},
    "Netherlands": {"en": "Netherlands", "uk": "Нідерланди"},
    "Belgium": {"en": "Belgium", "uk": "Бельгія"},
    "Portugal": {"en": "Portugal", "uk": "Португалія"},
    "Sweden": {"en": "Sweden", "uk": "Швеція"},
    "Norway": {"en": "Norway", "uk": "Норвегія"},
    "Denmark": {"en": "Denmark", "uk": "Данія"},
    "Finland": {"en": "Finland", "uk": "Фінляндія"},
    "Czech Republic": {"en": "Czech Republic", "uk": "Чехія"},
    "Slovakia": {"en": "Slovakia", "uk": "Словаччина"},
    "Romania": {"en": "Romania", "uk": "Румунія"},
    "Hungary": {"en": "Hungary", "uk": "Угорщина"},
}


class PersonalAssistantService:
    def __init__(self, storage: JsonStorage | None = None) -> None:
        self.storage = storage or JsonStorage()
        self.settings = self.storage.load_settings()
        self.data_path = self.storage.resolve_data_path(self.settings)
        self.data = self.storage.load_data(self.data_path)
        self._persist_settings()

    def _persist_settings(self) -> None:
        self.storage.save_settings(self.settings)

    def _autosave(self) -> None:
        self.storage.save_data(self.data, self.data_path)

    @staticmethod
    def _safe_dt(raw: str) -> datetime:
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return datetime.fromtimestamp(0)

    @staticmethod
    def _split_phone_value(raw_phone: str) -> Tuple[str, str]:
        prepared = str(raw_phone or "").strip()
        if not prepared:
            return "", ""

        match = re.match(r"^(\+\d{1,4})(?:[\s\-]+)?(.*)$", prepared)
        if match:
            code = match.group(1).strip()
            number = re.sub(r"[^0-9]", "", match.group(2))
            return code, number

        return "", re.sub(r"[^0-9]", "", prepared)

    @staticmethod
    def _compose_phone(code: str, number: str) -> str:
        prepared_code = str(code or "").strip()
        prepared_number = re.sub(r"[^0-9]", "", str(number or ""))
        if prepared_code and prepared_number:
            return f"{prepared_code} {prepared_number}"
        return prepared_code or prepared_number

    @staticmethod
    def _contact_identity_key(first_name: str, last_name: str) -> str:
        return "|".join(
            [
                normalize_name(first_name),
                normalize_name(last_name),
            ]
        )

    @staticmethod
    def _contact_sort_key(contact: Contact) -> Tuple[str, str, int]:
        return (
            contact.first_name.lower(),
            contact.last_name.lower(),
            contact.id,
        )

    @staticmethod
    def _safe_birthday(raw: Optional[str]) -> date:
        if not raw:
            return date.max
        try:
            return parse_date_flexible(raw)
        except ValueError:
            return date.max

    def _contact_index(self, contact_id: int) -> int:
        for index, contact in enumerate(self.data.contacts):
            if contact.id == contact_id:
                return index
        raise ValueError(f"Contact not found: {contact_id}")

    def _note_index(self, note_id: int) -> int:
        for index, note in enumerate(self.data.notes):
            if note.id == note_id:
                return index
        raise ValueError(f"Note not found: {note_id}")

    def get_contact(self, contact_id: int) -> Contact:
        return self.data.contacts[self._contact_index(contact_id)]

    def get_note(self, note_id: int) -> Note:
        return self.data.notes[self._note_index(note_id)]

    @staticmethod
    def _normalize_language(language: str) -> str:
        return "uk" if language == "uk" else "en"

    def country_from_display(self, country: str) -> str:
        prepared = country.strip()
        if not prepared:
            return ""
        if prepared in COUNTRY_PHONE_CODES:
            return prepared

        lowered = prepared.lower()
        for canonical, names in COUNTRY_LOCALIZED_NAMES.items():
            if names.get("en", "").lower() == lowered or names.get("uk", "").lower() == lowered:
                return canonical
        return prepared

    def country_to_display(self, country: str, language: str = "en") -> str:
        canonical = self.country_from_display(country)
        names = COUNTRY_LOCALIZED_NAMES.get(canonical)
        if not names:
            return country
        return names.get(self._normalize_language(language), canonical)

    def list_countries(self, language: str = "en") -> List[str]:
        lang = self._normalize_language(language)
        return sorted([names.get(lang, canonical) for canonical, names in COUNTRY_LOCALIZED_NAMES.items()])

    def get_country_phone_code(self, country: str) -> str:
        canonical = self.country_from_display(country)
        return COUNTRY_PHONE_CODES.get(canonical, "")

    def apply_country_code_to_phone(self, country: str, phone_value: str) -> str:
        canonical = self.country_from_display(country.strip())
        code = self.get_country_phone_code(canonical)
        prepared = str(phone_value or "").strip()
        if not code:
            return prepared
        if not prepared:
            return f"{code} "

        if prepared.startswith("+"):
            existing_code, number = self._split_phone_value(prepared)
            if existing_code == code:
                return self._compose_phone(existing_code, number)
            return prepared

        digits = re.sub(r"[^0-9]", "", prepared)
        if not digits:
            return f"{code} "

        code_digits = code.lstrip("+")
        if digits.startswith(code_digits):
            digits = digits[len(code_digits):]
        return self._compose_phone(code, digits)

    def _normalize_phone_for_storage(self, country: str, raw_phone: str) -> str:
        prepared_phone = str(raw_phone or "").strip()
        if not prepared_phone:
            return ""

        canonical_country = self.country_from_display(country.strip()) if country else ""
        if prepared_phone.startswith("+"):
            return validate_phone(prepared_phone)

        normalized_digits = validate_phone_number(prepared_phone)
        code = self.get_country_phone_code(canonical_country) if canonical_country else ""
        if code:
            return validate_phone(self._compose_phone(code, normalized_digits))
        return normalized_digits

    def get_contact_display_name(self, contact: Contact) -> str:
        parts = [contact.first_name.strip(), contact.last_name.strip()]
        full = " ".join(part for part in parts if part)
        return full or f"Contact {contact.id}"

    def get_contact_phone_display(self, contact: Contact) -> str:
        return contact.phone_number.strip()

    def _extract_from_legacy_phones(self, phones: Optional[List[str]]) -> str:
        if not phones:
            return ""
        for raw_phone in phones:
            prepared = str(raw_phone or "").strip()
            if not prepared:
                continue
            normalized = validate_phone(prepared)
            if normalized:
                code, number = self._split_phone_value(normalized)
                if code or number:
                    return self._compose_phone(code, number)
                return normalized
        return ""

    def _prepare_contact_payload(
        self,
        first_name: str = "",
        last_name: str = "",
        country: str = "",
        phone_number: str = "",
        email: Optional[str] = None,
        address: Optional[str] = None,
        birthday: Optional[str] = None,
        comment: str = "",
        favorite: bool = False,
        name: Optional[str] = None,
        phones: Optional[List[str]] = None,
        country_phone_code: str = "",
    ) -> Dict[str, object]:
        prepared_first_name_input = first_name or (name or "")

        legacy_phone = self._extract_from_legacy_phones(phones)
        prepared_phone_input = phone_number.strip()
        if not prepared_phone_input and legacy_phone:
            prepared_phone_input = legacy_phone

        if country_phone_code.strip() and prepared_phone_input and not prepared_phone_input.startswith("+"):
            prepared_phone_input = self._compose_phone(country_phone_code.strip(), prepared_phone_input)

        prepared_first_name = validate_required(prepared_first_name_input, "First name")
        prepared_last_name = last_name.strip()
        prepared_country = self.country_from_display(country.strip())
        prepared_phone_number = (
            self._normalize_phone_for_storage(prepared_country, prepared_phone_input) if prepared_phone_input else ""
        )

        return {
            "first_name": prepared_first_name,
            "last_name": prepared_last_name,
            "country": prepared_country,
            "phone_number": prepared_phone_number,
            "email": validate_email(email) if email else None,
            "address": address.strip() if address else None,
            "birthday": validate_birthday(birthday) if birthday else None,
            "comment": comment.strip(),
            "favorite": bool(favorite),
        }

    def _ensure_unique_contact_name(self, first_name: str, last_name: str, *, exclude_contact_id: int | None = None) -> None:
        key = self._contact_identity_key(first_name, last_name)
        for contact in self.data.contacts:
            if exclude_contact_id is not None and contact.id == exclude_contact_id:
                continue
            if self._contact_identity_key(contact.first_name, contact.last_name) == key:
                raise ValueError(f"Contact already exists: {first_name}")

    def list_contacts(self, query: str = "", filter_by: str = "all", sort_by: str = "name") -> List[Contact]:
        query_l = query.strip().lower()
        contacts = list(self.data.contacts)

        if query_l:
            filtered: List[Contact] = []
            for contact in contacts:
                haystack = [
                    contact.first_name.lower(),
                    contact.last_name.lower(),
                    contact.country.lower(),
                    self.country_to_display(contact.country, "en").lower(),
                    self.country_to_display(contact.country, "uk").lower(),
                    contact.phone_number.lower(),
                    (contact.email or "").lower(),
                ]
                if any(query_l in part for part in haystack):
                    filtered.append(contact)
            contacts = filtered

        if filter_by == "favorites":
            contacts = [contact for contact in contacts if contact.favorite]
        elif filter_by == "with_birthday":
            contacts = [contact for contact in contacts if contact.birthday]
        elif filter_by == "without_birthday":
            contacts = [contact for contact in contacts if not contact.birthday]

        if sort_by == "birthday":
            contacts.sort(key=lambda item: (item.birthday is None, self._safe_birthday(item.birthday), *self._contact_sort_key(item)))
        elif sort_by == "created":
            contacts.sort(key=lambda item: self._safe_dt(item.created_at), reverse=True)
        elif sort_by == "updated":
            contacts.sort(key=lambda item: self._safe_dt(item.updated_at), reverse=True)
        else:
            contacts.sort(key=self._contact_sort_key)

        return contacts

    def add_contact(
        self,
        first_name: str = "",
        last_name: str = "",
        country: str = "",
        phone_number: str = "",
        email: Optional[str] = None,
        address: Optional[str] = None,
        birthday: Optional[str] = None,
        comment: str = "",
        favorite: bool = False,
        name: Optional[str] = None,
        phones: Optional[List[str]] = None,
        nickname: str = "",  # legacy ignored
        country_phone_code: str = "",  # legacy supported as source for phone_number
    ) -> Contact:
        payload = self._prepare_contact_payload(
            first_name=first_name,
            last_name=last_name,
            country=country,
            phone_number=phone_number,
            email=email,
            address=address,
            birthday=birthday,
            comment=comment,
            favorite=favorite,
            name=name,
            phones=phones,
            country_phone_code=country_phone_code,
        )
        self._ensure_unique_contact_name(payload["first_name"], payload["last_name"])

        stamp = now_iso()
        contact = Contact(
            id=self.data.next_contact_id,
            first_name=str(payload["first_name"]),
            last_name=str(payload["last_name"]),
            country=str(payload["country"]),
            phone_number=str(payload["phone_number"]),
            email=payload["email"] if isinstance(payload["email"], str) else None,
            address=payload["address"] if isinstance(payload["address"], str) else None,
            birthday=payload["birthday"] if isinstance(payload["birthday"], str) else None,
            comment=str(payload["comment"]),
            favorite=bool(payload["favorite"]),
            created_at=stamp,
            updated_at=stamp,
        )
        self.data.contacts.append(contact)
        self.data.next_contact_id += 1
        self._autosave()
        return contact

    def update_contact(
        self,
        contact_id: int,
        first_name: str = "",
        last_name: str = "",
        country: str = "",
        phone_number: str = "",
        email: Optional[str] = None,
        address: Optional[str] = None,
        birthday: Optional[str] = None,
        comment: str = "",
        favorite: bool = False,
        name: Optional[str] = None,
        phones: Optional[List[str]] = None,
        nickname: str = "",  # legacy ignored
        country_phone_code: str = "",  # legacy supported as source for phone_number
    ) -> Contact:
        index = self._contact_index(contact_id)

        payload = self._prepare_contact_payload(
            first_name=first_name,
            last_name=last_name,
            country=country,
            phone_number=phone_number,
            email=email,
            address=address,
            birthday=birthday,
            comment=comment,
            favorite=favorite,
            name=name,
            phones=phones,
            country_phone_code=country_phone_code,
        )
        self._ensure_unique_contact_name(payload["first_name"], payload["last_name"], exclude_contact_id=contact_id)

        contact = self.data.contacts[index]
        contact.first_name = str(payload["first_name"])
        contact.last_name = str(payload["last_name"])
        contact.country = str(payload["country"])
        contact.phone_number = str(payload["phone_number"])
        contact.email = payload["email"] if isinstance(payload["email"], str) else None
        contact.address = payload["address"] if isinstance(payload["address"], str) else None
        contact.birthday = payload["birthday"] if isinstance(payload["birthday"], str) else None
        contact.comment = str(payload["comment"])
        contact.favorite = bool(payload["favorite"])
        contact.updated_at = now_iso()

        self._autosave()
        return contact

    def toggle_contact_favorite(self, contact_id: int) -> Contact:
        contact = self.get_contact(contact_id)
        contact.favorite = not contact.favorite
        contact.updated_at = now_iso()
        self._autosave()
        return contact

    def delete_contact(self, contact_id: int) -> None:
        index = self._contact_index(contact_id)
        del self.data.contacts[index]
        self._autosave()

    def upcoming_birthdays(self, days_ahead: int) -> List[Dict[str, object]]:
        if days_ahead < 0:
            raise ValueError("Days must be >= 0")

        today = datetime.now().date()
        results: List[Dict[str, object]] = []
        for contact in self.data.contacts:
            next_date = next_birthday_date(contact.birthday)
            if next_date is None:
                continue
            delta = (next_date - today).days
            if delta <= days_ahead:
                results.append(
                    {
                        "contact": contact,
                        "next_birthday": format_date(next_date),
                        "days_left": delta,
                    }
                )

        results.sort(key=lambda item: int(item["days_left"]))
        return results

    def list_notes(
        self,
        query: str = "",
        tag: str = "",
        filter_by: str = "all",
        sort_by: str = "updated",
    ) -> List[Note]:
        query_l = query.strip().lower()
        tag_l = tag.strip().lower()
        notes = list(self.data.notes)

        if query_l:
            notes = [
                note
                for note in notes
                if query_l in note.title.lower() or query_l in note.content.lower()
            ]

        if tag_l:
            notes = [note for note in notes if tag_l in note.tags]

        if filter_by == "pinned":
            notes = [note for note in notes if note.pinned]
        elif filter_by == "favorites":
            notes = [note for note in notes if note.favorite]

        if sort_by == "title":
            notes.sort(key=lambda item: item.title.lower())
        elif sort_by == "created":
            notes.sort(key=lambda item: self._safe_dt(item.created_at), reverse=True)
        else:
            notes.sort(key=lambda item: self._safe_dt(item.updated_at), reverse=True)

        return notes

    def add_note(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        pinned: bool = False,
        favorite: bool = False,
        color_label: str = "default",
    ) -> Note:
        prepared_title = validate_required(title, "Title")
        prepared_content = validate_required(content, "Content")

        stamp = now_iso()
        note = Note(
            id=self.data.next_note_id,
            title=prepared_title,
            content=prepared_content,
            tags=normalize_tags(tags or []),
            pinned=bool(pinned),
            favorite=bool(favorite),
            color_label=color_label.strip() or "default",
            created_at=stamp,
            updated_at=stamp,
        )
        self.data.notes.append(note)
        self.data.next_note_id += 1
        self._autosave()
        return note

    def update_note(
        self,
        note_id: int,
        title: str,
        content: str,
        tags: List[str],
        pinned: bool,
        favorite: bool,
        color_label: str,
    ) -> Note:
        index = self._note_index(note_id)
        note = self.data.notes[index]

        note.title = validate_required(title, "Title")
        note.content = validate_required(content, "Content")
        note.tags = normalize_tags(tags)
        note.pinned = bool(pinned)
        note.favorite = bool(favorite)
        note.color_label = color_label.strip() or "default"
        note.updated_at = now_iso()

        self._autosave()
        return note

    def toggle_note_pinned(self, note_id: int) -> Note:
        note = self.get_note(note_id)
        note.pinned = not note.pinned
        note.updated_at = now_iso()
        self._autosave()
        return note

    def toggle_note_favorite(self, note_id: int) -> Note:
        note = self.get_note(note_id)
        note.favorite = not note.favorite
        note.updated_at = now_iso()
        self._autosave()
        return note

    def delete_note(self, note_id: int) -> None:
        index = self._note_index(note_id)
        del self.data.notes[index]
        self._autosave()

    def global_search(self, query: str) -> Dict[str, List[object]]:
        return {
            "contacts": self.list_contacts(query=query),
            "notes": self.list_notes(query=query),
        }

    def dashboard_summary(self) -> Dict[str, object]:
        favorite_contacts = [contact for contact in self.data.contacts if contact.favorite]
        pinned_notes = [note for note in self.data.notes if note.pinned]

        pinned_notes_sorted = sorted(
            pinned_notes,
            key=lambda item: self._safe_dt(item.updated_at),
            reverse=True,
        )

        recent_records: List[Dict[str, object]] = []
        for contact in self.data.contacts:
            recent_records.append(
                {
                    "type": "contact",
                    "id": contact.id,
                    "title": self.get_contact_display_name(contact),
                    "updated_at": contact.updated_at,
                }
            )
        for note in self.data.notes:
            recent_records.append(
                {
                    "type": "note",
                    "id": note.id,
                    "title": note.title,
                    "updated_at": note.updated_at,
                }
            )

        recent_records.sort(key=lambda item: self._safe_dt(str(item["updated_at"])), reverse=True)

        return {
            "contacts_count": len(self.data.contacts),
            "notes_count": len(self.data.notes),
            "favorite_contacts_count": len(favorite_contacts),
            "pinned_notes_count": len(pinned_notes),
            "upcoming_birthdays": self.upcoming_birthdays(30)[:7],
            "pinned_notes": pinned_notes_sorted[:7],
            "recent_records": recent_records[:10],
        }

    def find_contact_by_name(self, name: str) -> Contact:
        key = normalize_name(name)
        for contact in self.data.contacts:
            if normalize_name(self.get_contact_display_name(contact)) == key:
                return contact
            if normalize_name(contact.first_name) == key:
                return contact
        raise ValueError(f"Contact not found: {name}")

    def edit_contact_by_name(
        self,
        name: str,
        new_name: Optional[str] = None,
        add_phones: Optional[List[str]] = None,
        remove_phones: Optional[List[str]] = None,
        set_email: Optional[str] = None,
        clear_email: bool = False,
        set_address: Optional[str] = None,
        clear_address: bool = False,
        set_birthday: Optional[str] = None,
        clear_birthday: bool = False,
        set_comment: Optional[str] = None,
        clear_comment: bool = False,
        favorite: Optional[bool] = None,
    ) -> Contact:
        contact = self.find_contact_by_name(name)
        phones = [self.get_contact_phone_display(contact)] if self.get_contact_phone_display(contact) else []

        if add_phones:
            phones.extend(add_phones)
        if remove_phones:
            remove_set = {value.strip() for value in remove_phones if value.strip()}
            phones = [value for value in phones if value not in remove_set]

        email = contact.email
        if clear_email:
            email = None
        elif set_email is not None:
            email = set_email

        address = contact.address
        if clear_address:
            address = None
        elif set_address is not None:
            address = set_address

        birthday = contact.birthday
        if clear_birthday:
            birthday = None
        elif set_birthday is not None:
            birthday = set_birthday

        comment = contact.comment
        if clear_comment:
            comment = ""
        elif set_comment is not None:
            comment = set_comment

        phone_number = contact.phone_number
        phones_payload: Optional[List[str]] = None
        if add_phones or remove_phones:
            phone_number = ""
            phones_payload = phones

        return self.update_contact(
            contact_id=contact.id,
            first_name=new_name or contact.first_name,
            last_name=contact.last_name,
            country=contact.country,
            phone_number=phone_number,
            phones=phones_payload,
            email=email,
            address=address,
            birthday=birthday,
            comment=comment,
            favorite=contact.favorite if favorite is None else favorite,
        )

    def delete_contact_by_name(self, name: str) -> None:
        self.delete_contact(self.find_contact_by_name(name).id)

    def search_contacts(self, query: str) -> List[Contact]:
        return self.list_contacts(query=query)

    def add_note_legacy(self, text: str, tags: Optional[List[str]] = None) -> Note:
        cleaned = validate_required(text, "Text")
        title = cleaned.splitlines()[0][:40]
        return self.add_note(title=title, content=cleaned, tags=tags)

    def edit_note_legacy(self, note_id: int, text: Optional[str] = None, tags: Optional[List[str]] = None) -> Note:
        note = self.get_note(note_id)
        return self.update_note(
            note_id=note_id,
            title=note.title,
            content=text if text is not None else note.content,
            tags=tags if tags is not None else note.tags,
            pinned=note.pinned,
            favorite=note.favorite,
            color_label=note.color_label,
        )

    def search_notes(self, query: Optional[str] = None, tag: Optional[str] = None) -> List[Note]:
        return self.list_notes(query=query or "", tag=tag or "")

    def sort_notes_by_tag(self, tag: str) -> List[Note]:
        tag_l = tag.strip().lower()
        with_tag = [note for note in self.data.notes if tag_l in note.tags]
        without_tag = [note for note in self.data.notes if tag_l not in note.tags]
        with_tag.sort(key=lambda item: self._safe_dt(item.updated_at), reverse=True)
        without_tag.sort(key=lambda item: self._safe_dt(item.updated_at), reverse=True)
        return with_tag + without_tag

    def export_json(self, destination: Path) -> None:
        self.storage.export_json(self.data, destination)

    def import_json(self, source: Path) -> None:
        self.data = self.storage.import_json(source)
        self._autosave()

    def create_backup(self) -> Path:
        return self.storage.create_backup(self.data, self.data_path)

    def set_language(self, language: str) -> None:
        if language not in {"en", "uk"}:
            raise ValueError("Unsupported language")
        self.settings.language = language
        self._persist_settings()

    def set_ui_density(self, density: str) -> None:
        if density not in {"compact", "normal"}:
            raise ValueError("Unsupported UI density")
        self.settings.ui_density = density
        self._persist_settings()

    def set_appearance_mode(self, mode: str) -> None:
        if mode not in {"light", "dark", "system"}:
            raise ValueError("Unsupported appearance mode")
        self.settings.appearance_mode = mode
        self._persist_settings()

    def set_data_path(self, path: Path) -> None:
        resolved = path.expanduser()
        if resolved.suffix.lower() != ".json":
            raise ValueError("Data file should have .json extension")

        if resolved.exists():
            self.data = self.storage.load_data(resolved)

        self.settings.data_path = str(resolved)
        self.data_path = resolved
        self._persist_settings()
        self._autosave()

    def get_data_path(self) -> Path:
        return self.data_path

    def get_data_folder(self) -> Path:
        return self.data_path.parent

