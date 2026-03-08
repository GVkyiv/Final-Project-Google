from typing import Dict, List, Tuple
import re

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


class CountryService:
    """Manages country lists and phone code translations."""

    @staticmethod
    def _normalize_language(language: str) -> str:
        return "uk" if language == "uk" else "en"

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
