from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from . import dialogs


class ContactsView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app) -> None:
        super().__init__(parent)
        self.app = app
        self.selected_contact_id: int | None = None

        self.query_var = tk.StringVar()
        self.filter_var = tk.StringVar()
        self.sort_var = tk.StringVar()

        self.first_name_var = tk.StringVar()
        self.last_name_var = tk.StringVar()
        self.country_var = tk.StringVar()
        self.phone_number_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.birthday_var = tk.StringVar()
        self.favorite_var = tk.BooleanVar(value=False)

        self.filter_value = "all"
        self.sort_value = "name"
        self._filter_map: dict[str, str] = {}
        self._sort_map: dict[str, str] = {}

        self._country_display_to_internal: dict[str, str] = {}
        self._country_internal_to_display: dict[str, str] = {}
        self._syncing_table_selection = False

        self._birthday_updating = False
        self.birthday_var.trace_add("write", self._on_birthday_text_changed)

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        self._build_layout()
        self.apply_translations()

    def _build_layout(self) -> None:
        pad = self.app.ui_tokens.outer_pad
        gap = self.app.ui_tokens.section_gap

        self.controls = ctk.CTkFrame(self, corner_radius=self.app.ui_tokens.corner_radius)
        self.controls.grid(row=0, column=0, columnspan=2, sticky="ew", padx=pad, pady=(pad, gap))
        self.controls.grid_columnconfigure(1, weight=1)

        self.query_label = ctk.CTkLabel(self.controls)
        self.query_label.grid(row=0, column=0, sticky="w", padx=(12, 6), pady=10)
        self.query_entry = ctk.CTkEntry(self.controls, textvariable=self.query_var)
        self.query_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)

        self.filter_label = ctk.CTkLabel(self.controls)
        self.filter_label.grid(row=0, column=2, sticky="w", padx=(0, 6), pady=10)
        self.filter_menu = ctk.CTkOptionMenu(self.controls, variable=self.filter_var, values=[], command=self._on_filter_changed)
        self.filter_menu.grid(row=0, column=3, padx=(0, 10), pady=10)

        self.sort_label = ctk.CTkLabel(self.controls)
        self.sort_label.grid(row=0, column=4, sticky="w", padx=(0, 6), pady=10)
        self.sort_menu = ctk.CTkOptionMenu(self.controls, variable=self.sort_var, values=[], command=self._on_sort_changed)
        self.sort_menu.grid(row=0, column=5, padx=(0, 10), pady=10)

        self.search_button = ctk.CTkButton(self.controls, width=96, command=self.refresh)
        self.search_button.grid(row=0, column=6, padx=(0, 8), pady=10)
        self.reset_button = ctk.CTkButton(self.controls, width=96, command=self._reset_filters)
        self.reset_button.grid(row=0, column=7, padx=(0, 12), pady=10)

        self.list_panel = ctk.CTkFrame(self, corner_radius=self.app.ui_tokens.corner_radius)
        self.list_panel.grid(row=1, column=0, sticky="nsew", padx=(pad, gap), pady=(0, pad))
        self.list_panel.grid_rowconfigure(1, weight=1)
        self.list_panel.grid_columnconfigure(0, weight=1)

        self.list_title = ctk.CTkLabel(self.list_panel, font=("Segoe UI Semibold", 16), anchor="w")
        self.list_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        self.table_frame = ctk.CTkFrame(self.list_panel, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        self.table = ttk.Treeview(
            self.table_frame,
            columns=("first_name", "last_name", "country", "phone", "email"),
            show="headings",
            selectmode="browse",
        )
        self.table.grid(row=0, column=0, sticky="nsew")
        self.table.column("first_name", width=140, anchor="w", stretch=True)
        self.table.column("last_name", width=140, anchor="w", stretch=True)
        self.table.column("country", width=150, anchor="w", stretch=True)
        self.table.column("phone", width=170, anchor="w", stretch=True)
        self.table.column("email", width=220, anchor="w", stretch=True)
        self.table.bind("<<TreeviewSelect>>", self._on_table_select)
        self.table.bind("<Double-1>", self._on_table_open)

        self.table_scrollbar = ctk.CTkScrollbar(self.table_frame, orientation="vertical", command=self.table.yview)
        self.table_scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.table.configure(yscrollcommand=self.table_scrollbar.set)

        self.form = ctk.CTkFrame(self, corner_radius=self.app.ui_tokens.corner_radius)
        self.form.grid(row=1, column=1, sticky="nsew", padx=(0, pad), pady=(0, pad))
        self.form.grid_columnconfigure(1, weight=1)
        self.form.grid_rowconfigure(8, weight=1)

        self.form_title = ctk.CTkLabel(self.form, font=("Segoe UI Semibold", 16), anchor="w")
        self.form_title.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 8))

        self.first_name_label = ctk.CTkLabel(self.form)
        self.first_name_label.grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)
        self.first_name_entry = ctk.CTkEntry(self.form, textvariable=self.first_name_var)
        self.first_name_entry.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.last_name_label = ctk.CTkLabel(self.form)
        self.last_name_label.grid(row=2, column=0, sticky="w", padx=(12, 6), pady=4)
        self.last_name_entry = ctk.CTkEntry(self.form, textvariable=self.last_name_var)
        self.last_name_entry.grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.country_label = ctk.CTkLabel(self.form)
        self.country_label.grid(row=3, column=0, sticky="w", padx=(12, 6), pady=4)
        self.country_combo = ctk.CTkComboBox(
            self.form,
            variable=self.country_var,
            values=[],
            command=self._on_country_changed,
            state="readonly",
        )
        self.country_combo.grid(row=3, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.phone_number_label = ctk.CTkLabel(self.form)
        self.phone_number_label.grid(row=4, column=0, sticky="w", padx=(12, 6), pady=4)
        self.phone_number_entry = ctk.CTkEntry(self.form, textvariable=self.phone_number_var)
        self.phone_number_entry.grid(row=4, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.email_label = ctk.CTkLabel(self.form)
        self.email_label.grid(row=5, column=0, sticky="w", padx=(12, 6), pady=4)
        self.email_entry = ctk.CTkEntry(self.form, textvariable=self.email_var)
        self.email_entry.grid(row=5, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.address_label = ctk.CTkLabel(self.form)
        self.address_label.grid(row=6, column=0, sticky="w", padx=(12, 6), pady=4)
        self.address_entry = ctk.CTkEntry(self.form, textvariable=self.address_var)
        self.address_entry.grid(row=6, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.birthday_label = ctk.CTkLabel(self.form)
        self.birthday_label.grid(row=7, column=0, sticky="w", padx=(12, 6), pady=4)
        self.birthday_entry = ctk.CTkEntry(self.form, textvariable=self.birthday_var)
        self.birthday_entry.grid(row=7, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.favorite_check = ctk.CTkCheckBox(self.form, variable=self.favorite_var, onvalue=True, offvalue=False)
        self.favorite_check.grid(row=8, column=1, sticky="w", padx=(0, 12), pady=4)

        self.comment_label = ctk.CTkLabel(self.form)
        self.comment_label.grid(row=9, column=0, sticky="nw", padx=(12, 6), pady=4)
        self.comment_text = ctk.CTkTextbox(self.form, height=110)
        self.comment_text.grid(row=9, column=1, sticky="nsew", padx=(0, 12), pady=4)

        self.button_row = ctk.CTkFrame(self.form, fg_color="transparent")
        self.button_row.grid(row=10, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 12))
        for idx in range(3):
            self.button_row.grid_columnconfigure(idx, weight=1)

        self.add_button = ctk.CTkButton(self.button_row, command=self.add_contact_and_new)
        self.add_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.save_button = ctk.CTkButton(self.button_row, command=self.save_contact)
        self.save_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.delete_button = ctk.CTkButton(self.button_row, command=self.delete_contact)
        self.delete_button.grid(row=0, column=2, padx=4, pady=4, sticky="ew")

        self.copy_phone_button = ctk.CTkButton(self.button_row, command=self.copy_phone)
        self.copy_phone_button.grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        self.copy_email_button = ctk.CTkButton(self.button_row, command=self.copy_email)
        self.copy_email_button.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        self.toggle_favorite_button = ctk.CTkButton(self.button_row, command=self.toggle_favorite)
        self.toggle_favorite_button.grid(row=1, column=2, padx=4, pady=4, sticky="ew")

        self.clear_button = ctk.CTkButton(self.button_row, command=self.start_add_contact)
        self.clear_button.grid(row=2, column=0, columnspan=3, padx=4, pady=4, sticky="ew")

    def _current_language(self) -> str:
        return self.app.i18n.language if hasattr(self.app, "i18n") else self.app.service.settings.language

    def _refresh_country_combo(self) -> None:
        language = self._current_language()
        current_internal = self.app.service.country_from_display(self.country_var.get())

        display_values = self.app.service.list_countries(language=language)
        self._country_display_to_internal.clear()
        self._country_internal_to_display.clear()

        for display_name in display_values:
            internal = self.app.service.country_from_display(display_name)
            self._country_display_to_internal[display_name] = internal
            self._country_internal_to_display[internal] = display_name

        self.country_combo.configure(values=display_values)

        if current_internal:
            self.country_var.set(self._country_internal_to_display.get(current_internal, current_internal))

    @staticmethod
    def _format_birthday_input(raw: str) -> str:
        digits = "".join(ch for ch in str(raw or "") if ch.isdigit())[:8]
        if not digits:
            return ""
        if len(digits) <= 2:
            return f"{digits}/" if len(digits) == 2 else digits
        if len(digits) <= 4:
            body = f"{digits[:2]}/{digits[2:]}"
            return f"{body}/" if len(digits) == 4 else body
        return f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"

    def _on_birthday_text_changed(self, *_args) -> None:
        if self._birthday_updating:
            return
        current = self.birthday_var.get()
        formatted = self._format_birthday_input(current)
        if formatted == current:
            return
        self._birthday_updating = True
        self.birthday_var.set(formatted)
        self._birthday_updating = False

    def apply_translations(self) -> None:
        t = self.app.t
        self.query_label.configure(text=t("query"))
        self.filter_label.configure(text=t("filter"))
        self.sort_label.configure(text=t("sort"))
        self.search_button.configure(text=t("search"))
        self.reset_button.configure(text=t("reset"))

        self.list_title.configure(text=t("contacts_list"))
        self.table.heading("first_name", text=t("first_name"))
        self.table.heading("last_name", text=t("last_name"))
        self.table.heading("country", text=t("country"))
        self.table.heading("phone", text=t("phone"))
        self.table.heading("email", text=t("email"))

        self.form_title.configure(text=t("contact_form"))
        self.first_name_label.configure(text=t("first_name"))
        self.last_name_label.configure(text=t("last_name"))
        self.country_label.configure(text=t("country"))
        self.phone_number_label.configure(text=t("phone"))
        self.email_label.configure(text=t("email"))
        self.address_label.configure(text=t("address"))
        self.birthday_label.configure(text=t("birthday_hint"))
        self.favorite_check.configure(text=t("favorite"))
        self.comment_label.configure(text=t("comment"))

        self.add_button.configure(text=t("add_contact"))
        self.save_button.configure(text=t("save"))
        self.delete_button.configure(text=t("delete"))
        self.copy_phone_button.configure(text=t("copy_phone"))
        self.copy_email_button.configure(text=t("copy_email"))
        self.toggle_favorite_button.configure(text=t("toggle_favorite"))
        self.clear_button.configure(text=t("clear"))

        self._refresh_country_combo()

        filter_options = [
            ("all", t("filter_all")),
            ("favorites", t("filter_favorites")),
            ("with_birthday", t("filter_with_birthday")),
            ("without_birthday", t("filter_without_birthday")),
        ]
        self._filter_map = {label: value for value, label in filter_options}
        filter_labels = [label for _, label in filter_options]
        self.filter_menu.configure(values=filter_labels)
        selected_filter = next(label for value, label in filter_options if value == self.filter_value)
        self.filter_var.set(selected_filter)

        sort_options = [
            ("name", t("sort_name")),
            ("birthday", t("sort_birthday")),
            ("created", t("sort_created")),
            ("updated", t("sort_updated")),
        ]
        self._sort_map = {label: value for value, label in sort_options}
        sort_labels = [label for _, label in sort_options]
        self.sort_menu.configure(values=sort_labels)
        selected_sort = next(label for value, label in sort_options if value == self.sort_value)
        self.sort_var.set(selected_sort)

    def refresh(self) -> None:
        contacts = self.app.service.list_contacts(
            query=self.query_var.get(),
            filter_by=self.filter_value,
            sort_by=self.sort_value,
        )

        for item_id in self.table.get_children():
            self.table.delete(item_id)

        if not contacts:
            self.table.insert("", "end", iid="empty", values=(self.app.t("no_contacts"), "", "", "", ""))
            return

        language = self._current_language()
        for contact in contacts:
            country = self.app.service.country_to_display(contact.country, language) if contact.country else "-"
            self.table.insert(
                "",
                "end",
                iid=str(contact.id),
                values=(
                    contact.first_name or "-",
                    contact.last_name or "-",
                    country,
                    self.app.service.get_contact_phone_display(contact) or "-",
                    contact.email or "-",
                ),
            )

        if self.selected_contact_id is not None:
            selected_iid = str(self.selected_contact_id)
            if selected_iid in self.table.get_children():
                self._set_table_selection(selected_iid)

    def _set_table_selection(self, row_id: str) -> None:
        self._syncing_table_selection = True
        try:
            self.table.selection_set(row_id)
            self.table.focus(row_id)
        finally:
            self._syncing_table_selection = False

    def _clear_table_selection(self) -> None:
        self._syncing_table_selection = True
        try:
            self.table.selection_remove(self.table.selection())
        finally:
            self._syncing_table_selection = False

    def _on_table_select(self, _event=None) -> None:
        if self._syncing_table_selection:
            return
        selected = self.table.selection()
        if not selected:
            return
        row_id = selected[0]
        if not row_id.isdigit():
            return
        self._fill_form(int(row_id))

    def _on_table_open(self, _event=None) -> None:
        selected = self.table.selection()
        if not selected:
            return
        row_id = selected[0]
        if not row_id.isdigit():
            return
        self._fill_form(int(row_id))

    def _on_filter_changed(self, _value: str | None = None) -> None:
        self.filter_value = self._filter_map.get(self.filter_var.get(), "all")
        self.refresh()

    def _on_sort_changed(self, _value: str | None = None) -> None:
        self.sort_value = self._sort_map.get(self.sort_var.get(), "name")
        self.refresh()

    def _on_country_changed(self, _value: str | None = None) -> None:
        country_display = self.country_var.get().strip()
        if not country_display:
            return
        country_internal = self._country_display_to_internal.get(
            country_display,
            self.app.service.country_from_display(country_display),
        )
        self.phone_number_var.set(
            self.app.service.apply_country_code_to_phone(country_internal, self.phone_number_var.get())
        )

    def _reset_filters(self) -> None:
        self.query_var.set("")
        self.filter_value = "all"
        self.sort_value = "name"
        self.apply_translations()
        self.refresh()

    def _fill_form(self, contact_id: int) -> None:
        try:
            contact = self.app.service.get_contact(contact_id)
        except ValueError:
            self.start_add_contact()
            self.refresh()
            return

        language = self._current_language()

        self.selected_contact_id = contact.id
        self.first_name_var.set(contact.first_name)
        self.last_name_var.set(contact.last_name)

        country_display = self._country_internal_to_display.get(
            contact.country,
            self.app.service.country_to_display(contact.country, language),
        )
        self.country_var.set(country_display)

        self.phone_number_var.set(contact.phone_number)
        self.email_var.set(contact.email or "")
        self.address_var.set(contact.address or "")
        self.birthday_var.set(contact.birthday or "")
        self.favorite_var.set(contact.favorite)
        self.comment_text.delete("1.0", "end")
        self.comment_text.insert("1.0", contact.comment)



    def start_add_contact(self) -> None:
        self.selected_contact_id = None
        self.first_name_var.set("")
        self.last_name_var.set("")
        self.country_var.set("")
        self.phone_number_var.set("")
        self.email_var.set("")
        self.address_var.set("")
        self.birthday_var.set("")
        self.favorite_var.set(False)
        self.comment_text.delete("1.0", "end")
        self._clear_table_selection()
        self.first_name_entry.focus_set()

    def _collect_form(self) -> dict:
        country_display = self.country_var.get().strip()
        country_internal = self._country_display_to_internal.get(
            country_display,
            self.app.service.country_from_display(country_display),
        )

        return {
            "first_name": self.first_name_var.get().strip(),
            "last_name": self.last_name_var.get().strip(),
            "country": country_internal,
            "phone_number": self.phone_number_var.get().strip(),
            "email": self.email_var.get().strip() or None,
            "address": self.address_var.get().strip() or None,
            "birthday": self.birthday_var.get().strip() or None,
            "comment": self.comment_text.get("1.0", "end").strip(),
            "favorite": self.favorite_var.get(),
        }

    def _payload_has_contact_data(self, payload: dict) -> bool:
        return any(
            [
                payload["first_name"],
                payload["last_name"],
                payload["country"],
                payload["phone_number"],
                payload["email"],
                payload["address"],
                payload["birthday"],
                payload["comment"],
                payload["favorite"],
            ]
        )

    def _payload_differs_contact(self, payload: dict, contact) -> bool:
        return any(
            [
                payload["first_name"] != contact.first_name,
                payload["last_name"] != contact.last_name,
                payload["country"] != contact.country,
                payload["phone_number"] != contact.phone_number,
                (payload["email"] or None) != (contact.email or None),
                (payload["address"] or None) != (contact.address or None),
                (payload["birthday"] or None) != (contact.birthday or None),
                payload["comment"] != contact.comment,
                bool(payload["favorite"]) != bool(contact.favorite),
            ]
        )

    def _save_current_contact_if_needed(self):
        payload = self._collect_form()

        if self.selected_contact_id is None:
            if not self._payload_has_contact_data(payload):
                return None
            return self.app.service.add_contact(**payload)

        contact = self.app.service.get_contact(self.selected_contact_id)
        if not self._payload_differs_contact(payload, contact):
            return None
        return self.app.service.update_contact(contact_id=self.selected_contact_id, **payload)

    def add_contact_and_new(self) -> None:
        try:
            contact = self._save_current_contact_if_needed()
            if contact is not None:
                self.app.notify_status(f"{self.app.t('save')}: {self.app.service.get_contact_display_name(contact)}")
            self.start_add_contact()
        except ValueError as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), self._localize_error(str(exc)))
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def _localize_error(self, text: str) -> str:
        message = text.strip()
        if message == "First name is required.":
            return self.app.t("error_first_name_required")
        if message.startswith("Invalid birthday format") or message.startswith("Invalid birthday value"):
            return self.app.t("error_birthday_format")
        if message.startswith("Invalid country phone code"):
            return self.app.t("error_phone_number")
        if message.startswith("Invalid phone number") or message.startswith("Phone number should contain"):
            return self.app.t("error_phone_number")
        return message

    def save_contact(self) -> None:
        try:
            payload = self._collect_form()
            if self.selected_contact_id is None:
                contact = self.app.service.add_contact(**payload)
            else:
                contact = self.app.service.update_contact(contact_id=self.selected_contact_id, **payload)

            self.refresh()
            self.select_contact(contact.id)
            self.app.notify_status(f"{self.app.t('save')}: {self.app.service.get_contact_display_name(contact)}")
        except ValueError as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), self._localize_error(str(exc)))
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def delete_contact(self) -> None:
        if self.selected_contact_id is None:
            dialogs.show_info(self.app.t("info"), self.app.t("select_contact_first"))
            return
        if not dialogs.ask_yes_no(self.app.t("info"), self.app.t("confirm_delete_contact")):
            return
        try:
            self.app.service.delete_contact(self.selected_contact_id)
            self.start_add_contact()
            self.refresh()
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def copy_phone(self) -> None:
        if self.selected_contact_id is None:
            dialogs.show_info(self.app.t("info"), self.app.t("select_contact_first"))
            return
        contact = self.app.service.get_contact(self.selected_contact_id)
        phone = self.app.service.get_contact_phone_display(contact)
        if not phone:
            return
        self.clipboard_clear()
        self.clipboard_append(phone)
        self.app.notify_status(self.app.t("copied_to_clipboard"))

    def copy_email(self) -> None:
        if self.selected_contact_id is None:
            dialogs.show_info(self.app.t("info"), self.app.t("select_contact_first"))
            return
        contact = self.app.service.get_contact(self.selected_contact_id)
        if not contact.email:
            return
        self.clipboard_clear()
        self.clipboard_append(contact.email)
        self.app.notify_status(self.app.t("copied_to_clipboard"))

    def toggle_favorite(self) -> None:
        if self.selected_contact_id is None:
            dialogs.show_info(self.app.t("info"), self.app.t("select_contact_first"))
            return
        contact = self.app.service.toggle_contact_favorite(self.selected_contact_id)
        self.favorite_var.set(contact.favorite)
        self.refresh()
        self.select_contact(contact.id)

    def select_contact(self, contact_id: int) -> None:
        self.selected_contact_id = contact_id
        selected_iid = str(contact_id)
        if selected_iid not in self.table.get_children():
            self.refresh()
            if selected_iid not in self.table.get_children():
                return
        self._set_table_selection(selected_iid)
        self._fill_form(contact_id)

