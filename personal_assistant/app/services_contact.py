from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from .exceptions import NotFoundError, ValidationError
from .models import Contact
from .services_country import CountryService
from .utils import format_date, next_birthday_date, normalize_name, now_iso, parse_date_flexible
from .validators import validate_birthday, validate_email, validate_phone, validate_phone_number, validate_required


class ContactService:
    def __init__(self, facade, country_service: CountryService) -> None:
        self.facade = facade
        self.country_service = country_service

    @property
    def data(self):
        return self.facade.data

    @staticmethod
    def _safe_dt(raw: str) -> datetime:
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return datetime.fromtimestamp(0)

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
        raise NotFoundError(f"Contact not found: {contact_id}")

    def get_contact(self, contact_id: int) -> Contact:
        return self.data.contacts[self._contact_index(contact_id)]

    def get_contact_display_name(self, contact: Contact) -> str:
        parts = [contact.first_name.strip(), contact.last_name.strip()]
        full = " ".join(part for part in parts if part)
        return full or f"Contact {contact.id}"

    def get_contact_phone_display(self, contact: Contact) -> str:
        return contact.phone_number.strip()

    def _normalize_phone_for_storage(self, country: str, raw_phone: str) -> str:
        prepared_phone = str(raw_phone or "").strip()
        if not prepared_phone:
            return ""

        canonical_country = self.country_service.country_from_display(country.strip()) if country else ""
        if prepared_phone.startswith("+"):
            return validate_phone(prepared_phone)

        normalized_digits = validate_phone_number(prepared_phone)
        code = self.country_service.get_country_phone_code(canonical_country) if canonical_country else ""
        if code:
            return validate_phone(self.country_service._compose_phone(code, normalized_digits))
        return normalized_digits

    def _extract_from_legacy_phones(self, phones: Optional[List[str]]) -> str:
        if not phones:
            return ""
        for raw_phone in phones:
            prepared = str(raw_phone or "").strip()
            if not prepared:
                continue
            normalized = validate_phone(prepared)
            if normalized:
                code, number = self.country_service._split_phone_value(normalized)
                if code or number:
                    return self.country_service._compose_phone(code, number)
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
            prepared_phone_input = self.country_service._compose_phone(country_phone_code.strip(), prepared_phone_input)

        prepared_first_name = validate_required(prepared_first_name_input, "First name")
        prepared_last_name = last_name.strip()
        prepared_country = self.country_service.country_from_display(country.strip())
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
                raise ValidationError(f"Contact already exists: {first_name}")

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
                    self.country_service.country_to_display(contact.country, "en").lower(),
                    self.country_service.country_to_display(contact.country, "uk").lower(),
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
        nickname: str = "",
        country_phone_code: str = "",
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
        self._ensure_unique_contact_name(str(payload["first_name"]), str(payload["last_name"]))

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
        self.facade._autosave()
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
        nickname: str = "",
        country_phone_code: str = "",
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
        self._ensure_unique_contact_name(str(payload["first_name"]), str(payload["last_name"]), exclude_contact_id=contact_id)

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

        self.facade._autosave()
        return contact

    def toggle_contact_favorite(self, contact_id: int) -> Contact:
        contact = self.get_contact(contact_id)
        contact.favorite = not contact.favorite
        contact.updated_at = now_iso()
        self.facade._autosave()
        return contact

    def delete_contact(self, contact_id: int) -> None:
        index = self._contact_index(contact_id)
        del self.data.contacts[index]
        self.facade._autosave()

    def upcoming_birthdays(self, days_ahead: int) -> List[Dict[str, object]]:
        if days_ahead < 0:
            raise ValidationError("Days must be >= 0")

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

    def find_contact_by_name(self, name: str) -> Contact:
        key = normalize_name(name)
        for contact in self.data.contacts:
            if normalize_name(self.get_contact_display_name(contact)) == key:
                return contact
            if normalize_name(contact.first_name) == key:
                return contact
        raise NotFoundError(f"Contact not found: {name}")

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
