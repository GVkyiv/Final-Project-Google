from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from . import dialogs


class BirthdaysView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app) -> None:
        super().__init__(parent)
        self.app = app
        self.days_var = tk.StringVar(value="30")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_layout()
        self.apply_translations()

    def _build_layout(self) -> None:
        pad = self.app.ui_tokens.outer_pad
        gap = self.app.ui_tokens.section_gap

        self.controls = ctk.CTkFrame(self, corner_radius=self.app.ui_tokens.corner_radius)
        self.controls.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, gap))

        self.days_label = ctk.CTkLabel(self.controls)
        self.days_label.grid(row=0, column=0, sticky="w", padx=(12, 6), pady=10)

        self.days_entry = ctk.CTkEntry(self.controls, textvariable=self.days_var, width=120)
        self.days_entry.grid(row=0, column=1, padx=(0, 8), pady=10)

        self.search_button = ctk.CTkButton(self.controls, width=96, command=self.refresh)
        self.search_button.grid(row=0, column=2, padx=(0, 12), pady=10)

        self.list_panel = ctk.CTkFrame(self, corner_radius=self.app.ui_tokens.corner_radius)
        self.list_panel.grid(row=1, column=0, sticky="nsew", padx=pad, pady=(0, pad))
        self.list_panel.grid_columnconfigure(0, weight=1)
        self.list_panel.grid_rowconfigure(1, weight=1)

        self.list_title = ctk.CTkLabel(self.list_panel, font=("Segoe UI Semibold", 16), anchor="w")
        self.list_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        self.table_frame = ctk.CTkFrame(self.list_panel, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        self.table = ttk.Treeview(
            self.table_frame,
            columns=("first_name", "last_name", "birthday", "days_left", "phone"),
            show="headings",
            selectmode="browse",
        )
        self.table.grid(row=0, column=0, sticky="nsew")
        self.table.column("first_name", width=150, anchor="w", stretch=True)
        self.table.column("last_name", width=150, anchor="w", stretch=True)
        self.table.column("birthday", width=120, anchor="center", stretch=False)
        self.table.column("days_left", width=90, anchor="center", stretch=False)
        self.table.column("phone", width=180, anchor="w", stretch=True)
        self.table.bind("<Double-1>", self._open_selected_contact)

        self.table_scrollbar = ctk.CTkScrollbar(self.table_frame, orientation="vertical", command=self.table.yview)
        self.table_scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.table.configure(yscrollcommand=self.table_scrollbar.set)

    def apply_translations(self) -> None:
        t = self.app.t
        self.days_label.configure(text=t("days_ahead"))
        self.search_button.configure(text=t("search"))
        self.list_title.configure(text=t("upcoming_birthdays"))

        self.table.heading("first_name", text=t("first_name"))
        self.table.heading("last_name", text=t("last_name"))
        self.table.heading("birthday", text=t("birthday"))
        self.table.heading("days_left", text=t("days_left"))
        self.table.heading("phone", text=t("phone"))

    def refresh(self) -> None:
        try:
            days = int(self.days_var.get().strip() or "0")
            rows = self.app.service.upcoming_birthdays(days)
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))
            return

        for item_id in self.table.get_children():
            self.table.delete(item_id)

        if not rows:
            self.table.insert("", "end", iid="empty", values=(self.app.t("no_birthdays"), "", "", "", ""))
            return

        for row in rows:
            contact = row["contact"]
            self.table.insert(
                "",
                "end",
                iid=str(contact.id),
                values=(
                    contact.first_name or "-",
                    contact.last_name or "-",
                    contact.birthday or "-",
                    str(row["days_left"]),
                    self.app.service.get_contact_phone_display(contact) or "-",
                ),
            )

    def _open_selected_contact(self, _event=None) -> None:
        selected = self.table.selection()
        if not selected:
            return
        row_id = selected[0]
        if not row_id.isdigit():
            return
        self.app.open_contact(int(row_id))

