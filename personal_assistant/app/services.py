from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import AppData, Contact, Note
from .services_contact import ContactService
from .services_country import CountryService
from .services_note import NoteService
from .services_settings import SettingsService
from .storage import JsonStorage

class PersonalAssistantService:
    def __init__(self, storage: JsonStorage | None = None) -> None:
        self.storage = storage or JsonStorage()
        self.settings = self.storage.load_settings()
        self.data_path = self.storage.resolve_data_path(self.settings)
        self.data = self.storage.load_data(self.data_path)

        self.country_service = CountryService()
        self.settings_service = SettingsService(self.storage, self)
        self.contact_service = ContactService(self, self.country_service)
        self.note_service = NoteService(self)

        self.settings_service._persist_settings()

    def _autosave(self) -> None:
        self.storage.save_data(self.data, self.data_path)

    @staticmethod
    def _safe_dt(raw: str) -> datetime:
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return datetime.fromtimestamp(0)

    # ---------------------------------------------------------
    # Settings / App Data
    # ---------------------------------------------------------
    def set_language(self, language: str) -> None:
        self.settings_service.set_language(language)

    def set_ui_density(self, density: str) -> None:
        self.settings_service.set_ui_density(density)

    def set_appearance_mode(self, mode: str) -> None:
        self.settings_service.set_appearance_mode(mode)

    def set_data_path(self, path: Path) -> None:
        self.settings_service.set_data_path(path)

    def get_data_path(self) -> Path:
        return self.data_path

    def get_data_folder(self) -> Path:
        return self.data_path.parent

    # ---------------------------------------------------------
    # Country logic
    # ---------------------------------------------------------
    def country_from_display(self, country: str) -> str:
        return self.country_service.country_from_display(country)

    def country_to_display(self, country: str, language: str = "en") -> str:
        return self.country_service.country_to_display(country, language)

    def list_countries(self, language: str = "en") -> List[str]:
        return self.country_service.list_countries(language)

    def get_country_phone_code(self, country: str) -> str:
        return self.country_service.get_country_phone_code(country)

    def apply_country_code_to_phone(self, country: str, phone_value: str) -> str:
        return self.country_service.apply_country_code_to_phone(country, phone_value)

    # ---------------------------------------------------------
    # Contacts
    # ---------------------------------------------------------
    def get_contact(self, contact_id: int) -> Contact:
        return self.contact_service.get_contact(contact_id)

    def get_contact_display_name(self, contact: Contact) -> str:
        return self.contact_service.get_contact_display_name(contact)

    def get_contact_phone_display(self, contact: Contact) -> str:
        return self.contact_service.get_contact_phone_display(contact)

    def list_contacts(self, query: str = "", filter_by: str = "all", sort_by: str = "name") -> List[Contact]:
        return self.contact_service.list_contacts(query, filter_by, sort_by)

    def add_contact(self, *args, **kwargs) -> Contact:
        return self.contact_service.add_contact(*args, **kwargs)

    def update_contact(self, contact_id: int, *args, **kwargs) -> Contact:
        return self.contact_service.update_contact(contact_id, *args, **kwargs)

    def toggle_contact_favorite(self, contact_id: int) -> Contact:
        return self.contact_service.toggle_contact_favorite(contact_id)

    def delete_contact(self, contact_id: int) -> None:
        self.contact_service.delete_contact(contact_id)

    def upcoming_birthdays(self, days_ahead: int) -> List[Dict[str, object]]:
        return self.contact_service.upcoming_birthdays(days_ahead)

    def find_contact_by_name(self, name: str) -> Contact:
        return self.contact_service.find_contact_by_name(name)

    def edit_contact_by_name(self, name: str, **kwargs) -> Contact:
        return self.contact_service.edit_contact_by_name(name, **kwargs)

    def delete_contact_by_name(self, name: str) -> None:
        self.contact_service.delete_contact_by_name(name)

    def search_contacts(self, query: str) -> List[Contact]:
        return self.contact_service.search_contacts(query)

    # ---------------------------------------------------------
    # Notes
    # ---------------------------------------------------------
    def get_note(self, note_id: int) -> Note:
        return self.note_service.get_note(note_id)

    def list_notes(self, query: str = "", tag: str = "", filter_by: str = "all", sort_by: str = "updated") -> List[Note]:
        return self.note_service.list_notes(query, tag, filter_by, sort_by)

    def add_note(self, *args, **kwargs) -> Note:
        return self.note_service.add_note(*args, **kwargs)

    def update_note(self, note_id: int, *args, **kwargs) -> Note:
        return self.note_service.update_note(note_id, *args, **kwargs)

    def toggle_note_pinned(self, note_id: int) -> Note:
        return self.note_service.toggle_note_pinned(note_id)

    def toggle_note_favorite(self, note_id: int) -> Note:
        return self.note_service.toggle_note_favorite(note_id)

    def delete_note(self, note_id: int) -> None:
        self.note_service.delete_note(note_id)

    def add_note_legacy(self, text: str, tags: Optional[List[str]] = None) -> Note:
        return self.note_service.add_note_legacy(text, tags)

    def edit_note_legacy(self, note_id: int, text: Optional[str] = None, tags: Optional[List[str]] = None) -> Note:
        return self.note_service.edit_note_legacy(note_id, text, tags)

    def search_notes(self, query: Optional[str] = None, tag: Optional[str] = None) -> List[Note]:
        return self.note_service.search_notes(query, tag)

    def sort_notes_by_tag(self, tag: str) -> List[Note]:
        return self.note_service.sort_notes_by_tag(tag)

    # ---------------------------------------------------------
    # Mixed / Cross-cutting
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Backup & Export
    # ---------------------------------------------------------
    def export_json(self, destination: Path) -> None:
        self.storage.export_json(self.data, destination)

    def import_json(self, source: Path) -> None:
        self.data = self.storage.import_json(source)
        self._autosave()

    def create_backup(self) -> Path:
        return self.storage.create_backup(self.data, self.data_path)
