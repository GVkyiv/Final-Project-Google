from __future__ import annotations

import tkinter as tk

import customtkinter as ctk


class SearchView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app) -> None:
        super().__init__(parent)
        self.app = app
        self.query_var = tk.StringVar()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_layout()
        self.apply_translations()

    def _build_layout(self) -> None:
        pad = self.app.ui_tokens.outer_pad
        gap = self.app.ui_tokens.section_gap

        self.controls = ctk.CTkFrame(self, corner_radius=self.app.ui_tokens.corner_radius)
        self.controls.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, gap))
        self.controls.grid_columnconfigure(1, weight=1)

        self.query_label = ctk.CTkLabel(self.controls)
        self.query_label.grid(row=0, column=0, sticky="w", padx=(12, 6), pady=10)

        self.query_entry = ctk.CTkEntry(self.controls, textvariable=self.query_var)
        self.query_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=10)
        self.query_entry.bind("<Return>", lambda _event: self._search())

        self.search_button = ctk.CTkButton(self.controls, width=96, command=self._search)
        self.search_button.grid(row=0, column=2, padx=(0, 12), pady=10)

        self.hint_label = ctk.CTkLabel(self.controls, anchor="w")
        self.hint_label.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 10))

        self.bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom.grid(row=1, column=0, sticky="nsew", padx=pad, pady=(0, pad))
        self.bottom.grid_columnconfigure(0, weight=1)
        self.bottom.grid_columnconfigure(1, weight=1)
        self.bottom.grid_rowconfigure(0, weight=1)

        self.contacts_frame = ctk.CTkFrame(self.bottom, corner_radius=self.app.ui_tokens.corner_radius)
        self.contacts_frame.grid(row=0, column=0, sticky="nsew", padx=(0, gap))
        self.contacts_frame.grid_columnconfigure(0, weight=1)
        self.contacts_frame.grid_rowconfigure(1, weight=1)

        self.contacts_title = ctk.CTkLabel(self.contacts_frame, font=("Segoe UI Semibold", 16), anchor="w")
        self.contacts_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        self.contacts_scroll = ctk.CTkScrollableFrame(self.contacts_frame, corner_radius=self.app.ui_tokens.corner_radius)
        self.contacts_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.contacts_scroll.grid_columnconfigure(0, weight=1)

        self.notes_frame = ctk.CTkFrame(self.bottom, corner_radius=self.app.ui_tokens.corner_radius)
        self.notes_frame.grid(row=0, column=1, sticky="nsew")
        self.notes_frame.grid_columnconfigure(0, weight=1)
        self.notes_frame.grid_rowconfigure(1, weight=1)

        self.notes_title = ctk.CTkLabel(self.notes_frame, font=("Segoe UI Semibold", 16), anchor="w")
        self.notes_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        self.notes_scroll = ctk.CTkScrollableFrame(self.notes_frame, corner_radius=self.app.ui_tokens.corner_radius)
        self.notes_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.notes_scroll.grid_columnconfigure(0, weight=1)

    def apply_translations(self) -> None:
        t = self.app.t
        self.query_label.configure(text=t("query"))
        self.search_button.configure(text=t("search"))
        self.hint_label.configure(text=t("search_hint"))

        self.contacts_title.configure(text=t("contacts_results"))
        self.notes_title.configure(text=t("notes_results"))

    def refresh(self) -> None:
        self._search()

    def run_search(self, query: str) -> None:
        self.query_var.set(query)
        self._search()

    def _search(self) -> None:
        query = self.query_var.get().strip()
        if not query:
            self._render_contacts([])
            self._render_notes([])
            return

        result = self.app.service.global_search(query)
        self._render_contacts(result["contacts"])
        self._render_notes(result["notes"])

    def _render_contacts(self, contacts) -> None:
        for widget in self.contacts_scroll.winfo_children():
            widget.destroy()

        if not contacts:
            empty = ctk.CTkLabel(self.contacts_scroll, text=self.app.t("no_results"), anchor="w")
            empty.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
            return

        for idx, contact in enumerate(contacts):
            country = self.app.service.country_to_display(contact.country, self.app.i18n.language) if contact.country else "-"
            button = ctk.CTkButton(
                self.contacts_scroll,
                text=(
                    f"{self.app.service.get_contact_display_name(contact)}\n"
                    f"{self.app.service.get_contact_phone_display(contact) or '-'} | {contact.email or '-'}\n"
                    f"{country}"
                ),
                anchor="w",
                height=70,
                corner_radius=self.app.ui_tokens.corner_radius,
                command=lambda cid=contact.id: self.app.open_contact(cid),
            )
            button.grid(row=idx, column=0, sticky="ew", padx=6, pady=4)

    def _render_notes(self, notes) -> None:
        for widget in self.notes_scroll.winfo_children():
            widget.destroy()

        if not notes:
            empty = ctk.CTkLabel(self.notes_scroll, text=self.app.t("no_results"), anchor="w")
            empty.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
            return

        for idx, note in enumerate(notes):
            tags = ", ".join(note.tags) if note.tags else "-"
            preview = note.content.replace("\n", " ").strip()
            if len(preview) > 64:
                preview = f"{preview[:64]}..."

            button = ctk.CTkButton(
                self.notes_scroll,
                text=f"{note.title}\n{preview}\n{tags} | {note.updated_at}",
                anchor="w",
                height=74,
                corner_radius=self.app.ui_tokens.corner_radius,
                command=lambda nid=note.id: self.app.open_note(nid),
            )
            button.grid(row=idx, column=0, sticky="ew", padx=6, pady=4)

