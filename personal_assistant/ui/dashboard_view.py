from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from . import dialogs


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app) -> None:
        super().__init__(parent)
        self.app = app

        self.stats_vars = {
            "contacts_count": tk.StringVar(value="0"),
            "notes_count": tk.StringVar(value="0"),
            "favorite_contacts_count": tk.StringVar(value="0"),
            "pinned_notes_count": tk.StringVar(value="0"),
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=0) # Quick Actions
        self.grid_rowconfigure(1, weight=0) # Stats
        self.grid_rowconfigure(2, weight=1) # Bottom (Birthdays + Pinned/Recent)
        self.grid_rowconfigure(3, weight=1) # New row for the new layout

        self._build_layout()
        self.apply_translations()

    def _build_layout(self) -> None:
        pad = self.app.ui_tokens.outer_pad
        gap = self.app.ui_tokens.section_gap

        # Quick Actions Frame
        self.quick_frame = ctk.CTkFrame(self, corner_radius=self.app.ui_tokens.card_corner_radius)
        self.quick_frame.grid(row=0, column=0, sticky="ew", padx=pad, pady=(pad, gap))
        self.quick_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.quick_title = ctk.CTkLabel(self.quick_frame, font=("Segoe UI Semibold", 16), anchor="w")
        self.quick_title.grid(row=0, column=0, columnspan=4, sticky="ew", padx=12, pady=(10, 8))

        self.quick_buttons = {
            "add_contact": ctk.CTkButton(self.quick_frame, height=42, command=self.app.open_contact_new),
            "add_note": ctk.CTkButton(self.quick_frame, height=42, command=self.app.open_note_new),
            "export_data": ctk.CTkButton(self.quick_frame, height=42, command=self._export_data),
            "backup": ctk.CTkButton(self.quick_frame, height=42, command=self._create_backup),
        }
        for idx, key in enumerate(["add_contact", "add_note", "export_data", "backup"]):
            self.quick_buttons[key].grid(row=1, column=idx, padx=8, pady=(0, 12), sticky="ew")

        # Stats Frame
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=pad, pady=(0, gap))
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_labels: dict[str, ctk.CTkLabel] = {}
        for idx, key in enumerate(self.stats_vars):
            card = ctk.CTkFrame(self.stats_frame, corner_radius=self.app.ui_tokens.card_corner_radius)
            card.grid(row=0, column=idx, padx=(0 if idx == 0 else 8, 0), sticky="nsew")
            title = ctk.CTkLabel(card, anchor="w")
            title.pack(fill="x", padx=12, pady=(10, 2))
            value = ctk.CTkLabel(card, textvariable=self.stats_vars[key], font=("Segoe UI Semibold", 30), anchor="w")
            value.pack(fill="x", padx=12, pady=(0, 10))
            self.stat_labels[key] = title

        # Bottom section (Birthdays, Pinned, Recent)
        self.bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom.grid(row=2, column=0, sticky="nsew", padx=pad, pady=(0, pad))
        self.bottom.grid_columnconfigure(0, weight=2)
        self.bottom.grid_columnconfigure(1, weight=1)
        self.bottom.grid_rowconfigure(0, weight=1)

        # Birthdays Frame
        self.birthdays_frame = ctk.CTkFrame(self.bottom, corner_radius=self.app.ui_tokens.card_corner_radius)
        self.birthdays_frame.grid(row=0, column=0, sticky="nsew", padx=(0, gap))
        self.birthdays_frame.grid_columnconfigure(0, weight=1)
        self.birthdays_frame.grid_rowconfigure(1, weight=1)

        self.birthdays_title = ctk.CTkLabel(self.birthdays_frame, font=("Segoe UI Semibold", 16), anchor="w")
        self.birthdays_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        self.birthdays_table_frame = ctk.CTkFrame(self.birthdays_frame, fg_color="transparent")
        self.birthdays_table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.birthdays_table_frame.grid_rowconfigure(0, weight=1)
        self.birthdays_table_frame.grid_columnconfigure(0, weight=1)

        self.birthdays_table = ttk.Treeview(
            self.birthdays_table_frame,
            columns=("first_name", "last_name", "birthday", "phone"),
            show="headings",
            selectmode="browse",
        )
        self.birthdays_table.grid(row=0, column=0, sticky="nsew")
        self.birthdays_table.column("first_name", width=140, anchor="w", stretch=True)
        self.birthdays_table.column("last_name", width=140, anchor="w", stretch=True)
        self.birthdays_table.column("birthday", width=120, anchor="center", stretch=False)
        self.birthdays_table.column("phone", width=180, anchor="w", stretch=True)
        self.birthdays_table.bind("<Double-1>", self._open_selected_birthday_contact)

        self.birthdays_scrollbar = ctk.CTkScrollbar(self.birthdays_table_frame, orientation="vertical", command=self.birthdays_table.yview)
        self.birthdays_scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.birthdays_table.configure(yscrollcommand=self.birthdays_scrollbar.set)

        # Right section (Pinned, Recent)
        self.right = ctk.CTkFrame(self.bottom, fg_color="transparent")
        self.right.grid(row=0, column=1, sticky="nsew")
        self.right.grid_rowconfigure(0, weight=1)
        self.right.grid_rowconfigure(1, weight=1)
        self.right.grid_columnconfigure(0, weight=1)

        # Pinned Notes Frame
        self.pinned_frame = ctk.CTkFrame(self.right, corner_radius=self.app.ui_tokens.card_corner_radius)
        self.pinned_frame.grid(row=0, column=0, sticky="nsew", pady=(0, gap))
        self.pinned_frame.grid_columnconfigure(0, weight=1)
        self.pinned_frame.grid_rowconfigure(1, weight=1)

        self.pinned_title = ctk.CTkLabel(self.pinned_frame, font=("Segoe UI Semibold", 15), anchor="w")
        self.pinned_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        self.pinned_scroll = ctk.CTkScrollableFrame(self.pinned_frame, corner_radius=self.app.ui_tokens.corner_radius)
        self.pinned_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.pinned_scroll.grid_columnconfigure(0, weight=1)

        # Recent Records Frame
        self.recent_frame = ctk.CTkFrame(self.right, corner_radius=self.app.ui_tokens.card_corner_radius)
        self.recent_frame.grid(row=1, column=0, sticky="nsew")
        self.recent_frame.grid_columnconfigure(0, weight=1)
        self.recent_frame.grid_rowconfigure(1, weight=1)

        self.recent_title = ctk.CTkLabel(self.recent_frame, font=("Segoe UI Semibold", 15), anchor="w")
        self.recent_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        self.recent_scroll = ctk.CTkScrollableFrame(self.recent_frame, corner_radius=self.app.ui_tokens.corner_radius)
        self.recent_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.recent_scroll.grid_columnconfigure(0, weight=1)

    def apply_translations(self) -> None:
        t = self.app.t
        self.quick_title.configure(text=t("quick_actions"))
        self.quick_buttons["add_contact"].configure(text=t("add_contact"))
        self.quick_buttons["add_note"].configure(text=t("add_note"))
        self.quick_buttons["export_data"].configure(text=t("export_data"))
        self.quick_buttons["backup"].configure(text=t("backup"))

        for key, label in self.stat_labels.items():
            label.configure(text=t(key))

        self.birthdays_title.configure(text=t("upcoming_birthdays"))
        self.birthdays_table.heading("first_name", text=t("first_name"))
        self.birthdays_table.heading("last_name", text=t("last_name"))
        self.birthdays_table.heading("birthday", text=t("birthday"))
        self.birthdays_table.heading("phone", text=t("phone"))

        self.pinned_title.configure(text=t("pinned_notes"))
        self.recent_title.configure(text=t("recent_records"))

    def refresh(self) -> None:
        data = self.app.service.dashboard_summary()
        for key in self.stats_vars:
            self.stats_vars[key].set(str(data[key]))

        self._render_birthdays(data["upcoming_birthdays"])
        self._render_pinned_notes(data["pinned_notes"])
        self._render_recent(data["recent_records"])

    def _render_birthdays(self, rows) -> None:
        for item_id in self.birthdays_table.get_children():
            self.birthdays_table.delete(item_id)

        if not rows:
            self.birthdays_table.insert("", "end", iid="empty", values=(self.app.t("no_birthdays"), "", "", ""))
            return

        for item in rows:
            contact = item["contact"]
            self.birthdays_table.insert(
                "",
                "end",
                iid=str(contact.id),
                values=(
                    contact.first_name or "-",
                    contact.last_name or "-",
                    contact.birthday or "-",
                    self.app.service.get_contact_phone_display(contact) or "-",
                ),
            )

    def _open_selected_birthday_contact(self, _event=None) -> None:
        selected = self.birthdays_table.selection()
        if not selected:
            return
        row_id = selected[0]
        if not row_id.isdigit():
            return
        self.app.open_contact(int(row_id))

    def _render_pinned_notes(self, notes) -> None:
        for widget in self.pinned_scroll.winfo_children():
            widget.destroy()

        if not notes:
            empty = ctk.CTkLabel(self.pinned_scroll, text=self.app.t("no_pinned_notes"), anchor="w")
            empty.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
            return

        for idx, note in enumerate(notes):
            button = ctk.CTkButton(
                self.pinned_scroll,
                text=f"{note.title}\n{self.app.t('updated_at')}: {note.updated_at}",
                anchor="w",
                height=62,
                corner_radius=self.app.ui_tokens.corner_radius,
                command=lambda nid=note.id: self.app.open_note(nid),
            )
            button.grid(row=idx, column=0, sticky="ew", padx=6, pady=4)

    def _render_recent(self, records) -> None:
        for widget in self.recent_scroll.winfo_children():
            widget.destroy()

        if not records:
            empty = ctk.CTkLabel(self.recent_scroll, text=self.app.t("no_recent_records"), anchor="w")
            empty.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
            return

        for idx, item in enumerate(records):
            kind = item["type"]
            text = f"[{kind}] {item['title']}\n{self.app.t('updated_at')}: {item['updated_at']}"
            if kind == "contact":
                command = lambda cid=item["id"]: self.app.open_contact(int(cid))
            else:
                command = lambda nid=item["id"]: self.app.open_note(int(nid))

            button = ctk.CTkButton(
                self.recent_scroll,
                text=text,
                anchor="w",
                height=58,
                corner_radius=self.app.ui_tokens.corner_radius,
                command=command,
            )
            button.grid(row=idx, column=0, sticky="ew", padx=6, pady=4)

    def _export_data(self) -> None:
        path = dialogs.ask_export_path(self.app.service.get_data_folder())
        if not path:
            return
        try:
            self.app.service.export_json(Path(path))
            dialogs.show_info(self.app.t("info"), self.app.t("export_done"))
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def _create_backup(self) -> None:
        try:
            backup = self.app.service.create_backup()
            dialogs.show_info(self.app.t("info"), f"{self.app.t('backup_created')} {backup}")
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

