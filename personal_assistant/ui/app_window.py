from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from personal_assistant.app.services import PersonalAssistantService
from personal_assistant.app.theme import UiTokens, apply_theme
from personal_assistant.app.translations import I18n
from .birthdays_view import BirthdaysView
from .contacts_view import ContactsView
from .dashboard_view import DashboardView
from .notes_view import NotesView
from .search_view import SearchView
from .settings_view import SettingsView


class AppWindow(ctk.CTk):
    def __init__(self, service: PersonalAssistantService | None = None) -> None:
        super().__init__()
        self.service = service or PersonalAssistantService()
        self.i18n = I18n(self.service.settings.language)
        self.current_page = "dashboard"

        self.status_var = tk.StringVar(value="")
        self.page_title_var = tk.StringVar(value="")
        self.language_var = tk.StringVar()

        self._lang_map: dict[str, str] = {}
        self._language_updating = False
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self._nav_order = [
            ("dashboard", "\U0001F3E0"),
            ("contacts", "\U0001F465"),
            ("notes", "\U0001F4DD"),
            ("birthdays", "\U0001F4C5"),
            ("search", "\U0001F50D"),
            ("settings", "\u2699\uFE0F"),
        ]
        self.title(self.t("app_title"))
        self.geometry("1360x840")
        self.minsize(1180, 760)

        self.ui_tokens: UiTokens = apply_theme(
            self,
            self.service.settings.ui_density,
            getattr(self.service.settings, "appearance_mode", "system"),
        )

        self._build_layout()
        self.i18n.bind(self.apply_translations)
        self.apply_translations()
        self.refresh_all()
        self.show_page("dashboard")

    def t(self, key: str) -> str:
        return self.i18n.t(key)

    def notify_status(self, text: str) -> None:
        self.status_var.set(text)

    def _build_layout(self) -> None:
        pad = self.ui_tokens.outer_pad
        gap = self.ui_tokens.section_gap

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=("#F8FAFC", "#0F172A"))
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(len(self._nav_order) + 1, weight=1)

        self.brand_label = ctk.CTkLabel(
            self.sidebar,
            text=self.t("app_title"),
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            anchor="center",
        )
        self.brand_label.grid(row=0, column=0, sticky="ew", padx=18, pady=(28, 28))

        for idx, (page, icon) in enumerate(self._nav_order, start=1):
            button = ctk.CTkButton(
                self.sidebar,
                text="",
                anchor="w",
                height=44,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                corner_radius=self.ui_tokens.corner_radius,
                command=lambda value=page: self.show_page(value),
            )
            button.grid(row=idx, column=0, sticky="ew", padx=16, pady=(0, 10))
            self._nav_buttons[page] = button

        self.topbar = ctk.CTkFrame(self, fg_color="transparent")
        self.topbar.grid(row=0, column=1, sticky="ew", padx=(gap, pad), pady=(pad, gap))
        self.topbar.grid_columnconfigure(0, weight=1)

        self.page_title_label = ctk.CTkLabel(
            self.topbar,
            textvariable=self.page_title_var,
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            anchor="w",
            text_color=("#0F172A", "#F8FAFC"),
        )
        self.page_title_label.grid(row=0, column=0, sticky="w", padx=(16, 10), pady=12)

        self.language_label = ctk.CTkLabel(self.topbar, anchor="e")
        self.language_label.grid(row=0, column=1, sticky="e", padx=(4, 6), pady=10)

        self.language_menu = ctk.CTkOptionMenu(
            self.topbar,
            variable=self.language_var,
            values=[],
            width=130,
            command=self._on_language_changed,
        )
        self.language_menu.grid(row=0, column=2, sticky="e", padx=(0, 14), pady=10)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=1, sticky="nsew", padx=(gap, pad), pady=(0, gap))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w")
        self.status_label.grid(row=2, column=1, sticky="ew", padx=(gap, pad), pady=(0, pad))

        self.pages = {
            "dashboard": DashboardView(self.content, self),
            "contacts": ContactsView(self.content, self),
            "notes": NotesView(self.content, self),
            "birthdays": BirthdaysView(self.content, self),
            "search": SearchView(self.content, self),
            "settings": SettingsView(self.content, self),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def apply_translations(self) -> None:
        self.title(self.t("app_title"))
        self.brand_label.configure(text=self.t("app_title"))

        for page, icon in self._nav_order:
            self._nav_buttons[page].configure(text=f"{icon} {self.t(page)}")

        self.language_label.configure(text=f"{self.t('language')}:")

        language_options = [
            ("en", self.t("language_english")),
            ("uk", self.t("language_ukrainian")),
        ]
        self._lang_map = {label: code for code, label in language_options}
        self.language_menu.configure(values=[label for _, label in language_options])

        current_lang = self.i18n.language
        current_label = next(label for code, label in language_options if code == current_lang)
        self._language_updating = True
        self.language_var.set(current_label)
        self._language_updating = False

        self.show_page(self.current_page)
        self.notify_status(self.t("status_ready"))

        for page in self.pages.values():
            page.apply_translations()

    def _update_nav_state(self) -> None:
        accent = self.ui_tokens.accent_color
        for page, button in self._nav_buttons.items():
            if page == self.current_page:
                button.configure(
                    fg_color=accent,
                    text_color=("#FFFFFF", "#FFFFFF"),
                    hover_color=accent,
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=("#475569", "#94A3B8"),
                    hover_color=("#E2E8F0", "#1E293B"),
                )

    def show_page(self, page: str) -> None:
        if page not in self.pages:
            return
        self.current_page = page
        self.pages[page].tkraise()
        self.pages[page].refresh()
        self.page_title_var.set(self.t(page))
        self._update_nav_state()

    def refresh_all(self) -> None:
        for page in self.pages.values():
            page.refresh()

    def open_contact(self, contact_id: int) -> None:
        self.show_page("contacts")
        self.pages["contacts"].select_contact(contact_id)

    def open_contact_new(self) -> None:
        self.show_page("contacts")
        self.pages["contacts"].start_add_contact()

    def open_note(self, note_id: int) -> None:
        self.show_page("notes")
        self.pages["notes"].select_note(note_id)

    def open_note_new(self) -> None:
        self.show_page("notes")
        self.pages["notes"].start_add_note()

    def _on_language_changed(self, _value: str | None = None) -> None:
        if self._language_updating:
            return
        code = self._lang_map.get(self.language_var.get())
        if not code:
            return
        try:
            self.service.set_language(code)
            self.i18n.set_language(code)
        except Exception as exc:  # pragma: no cover - GUI runtime
            self.notify_status(str(exc))

    def set_density(self, density: str) -> None:
        try:
            self.service.set_ui_density(density)
            self.ui_tokens = apply_theme(
                self,
                self.service.settings.ui_density,
                getattr(self.service.settings, "appearance_mode", "system"),
            )
            self.refresh_all()
        except Exception as exc:  # pragma: no cover - GUI runtime
            self.notify_status(str(exc))

    def set_appearance_mode(self, mode: str) -> None:
        try:
            self.service.set_appearance_mode(mode)
            self.ui_tokens = apply_theme(self, self.service.settings.ui_density, mode)
            self.refresh_all()
        except Exception as exc:  # pragma: no cover - GUI runtime
            self.notify_status(str(exc))

