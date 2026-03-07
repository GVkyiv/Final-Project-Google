from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk

from personal_assistant.app.utils import format_date, parse_date_flexible, split_csv
from . import dialogs


class NotesView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app) -> None:
        super().__init__(parent)
        self.app = app
        self.selected_note_id: int | None = None

        self.query_var = tk.StringVar()
        self.tag_var = tk.StringVar()
        self.filter_var = tk.StringVar()
        self.sort_var = tk.StringVar()

        self.title_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.color_label_var = tk.StringVar(value="default")
        self.pinned_var = tk.BooleanVar(value=False)
        self.favorite_var = tk.BooleanVar(value=False)
        self.created_at_var = tk.StringVar()
        self.updated_at_var = tk.StringVar()

        self.filter_value = "all"
        self.sort_value = "updated"
        self._filter_map: dict[str, str] = {}
        self._sort_map: dict[str, str] = {}
        self._syncing_table_selection = False

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
        self.controls.grid_columnconfigure(3, weight=1)

        self.query_label = ctk.CTkLabel(self.controls)
        self.query_label.grid(row=0, column=0, sticky="w", padx=(12, 6), pady=10)
        self.query_entry = ctk.CTkEntry(self.controls, textvariable=self.query_var)
        self.query_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)

        self.tag_label = ctk.CTkLabel(self.controls)
        self.tag_label.grid(row=0, column=2, sticky="w", padx=(0, 6), pady=10)
        self.tag_entry = ctk.CTkEntry(self.controls, textvariable=self.tag_var)
        self.tag_entry.grid(row=0, column=3, sticky="ew", padx=(0, 10), pady=10)

        self.filter_label = ctk.CTkLabel(self.controls)
        self.filter_label.grid(row=0, column=4, sticky="w", padx=(0, 6), pady=10)
        self.filter_menu = ctk.CTkOptionMenu(self.controls, variable=self.filter_var, values=[], command=self._on_filter_changed)
        self.filter_menu.grid(row=0, column=5, padx=(0, 10), pady=10)

        self.sort_label = ctk.CTkLabel(self.controls)
        self.sort_label.grid(row=0, column=6, sticky="w", padx=(0, 6), pady=10)
        self.sort_menu = ctk.CTkOptionMenu(self.controls, variable=self.sort_var, values=[], command=self._on_sort_changed)
        self.sort_menu.grid(row=0, column=7, padx=(0, 10), pady=10)

        self.search_button = ctk.CTkButton(self.controls, width=96, command=self.refresh)
        self.search_button.grid(row=0, column=8, padx=(0, 8), pady=10)
        self.reset_button = ctk.CTkButton(self.controls, width=96, command=self._reset_filters)
        self.reset_button.grid(row=0, column=9, padx=(0, 12), pady=10)

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
            columns=("title", "content", "tags", "created_date"),
            show="headings",
            selectmode="browse",
        )
        self.table.grid(row=0, column=0, sticky="nsew")
        self.table.column("title", width=180, anchor="w", stretch=True)
        self.table.column("content", width=320, anchor="w", stretch=True)
        self.table.column("tags", width=180, anchor="w", stretch=True)
        self.table.column("created_date", width=130, anchor="center", stretch=False)
        self.table.bind("<<TreeviewSelect>>", self._on_table_select)
        self.table.bind("<Double-1>", self._on_table_open)

        self.table_scrollbar = ctk.CTkScrollbar(self.table_frame, orientation="vertical", command=self.table.yview)
        self.table_scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.table.configure(yscrollcommand=self.table_scrollbar.set)

        self.form = ctk.CTkFrame(self, corner_radius=self.app.ui_tokens.corner_radius)
        self.form.grid(row=1, column=1, sticky="nsew", padx=(0, pad), pady=(0, pad))
        self.form.grid_columnconfigure(1, weight=1)
        self.form.grid_rowconfigure(2, weight=1)

        self.form_title = ctk.CTkLabel(self.form, font=("Segoe UI Semibold", 16), anchor="w")
        self.form_title.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 8))

        self.title_label = ctk.CTkLabel(self.form)
        self.title_label.grid(row=1, column=0, sticky="w", padx=(12, 6), pady=4)
        self.title_entry = ctk.CTkEntry(self.form, textvariable=self.title_var)
        self.title_entry.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.content_label = ctk.CTkLabel(self.form)
        self.content_label.grid(row=2, column=0, sticky="nw", padx=(12, 6), pady=4)
        self.content_text = ctk.CTkTextbox(self.form, height=180)
        self.content_text.grid(row=2, column=1, sticky="nsew", padx=(0, 12), pady=4)

        self.tags_label = ctk.CTkLabel(self.form)
        self.tags_label.grid(row=3, column=0, sticky="w", padx=(12, 6), pady=4)
        self.tags_entry = ctk.CTkEntry(self.form, textvariable=self.tags_var)
        self.tags_entry.grid(row=3, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.color_label = ctk.CTkLabel(self.form)
        self.color_label.grid(row=4, column=0, sticky="w", padx=(12, 6), pady=4)
        self.color_combo = ctk.CTkComboBox(
            self.form,
            variable=self.color_label_var,
            state="readonly",
            values=["default", "blue", "green", "yellow", "red"],
        )
        self.color_combo.grid(row=4, column=1, sticky="ew", padx=(0, 12), pady=4)

        self.pinned_check = ctk.CTkCheckBox(self.form, variable=self.pinned_var, onvalue=True, offvalue=False)
        self.pinned_check.grid(row=5, column=1, sticky="w", padx=(0, 12), pady=4)

        self.favorite_check = ctk.CTkCheckBox(self.form, variable=self.favorite_var, onvalue=True, offvalue=False)
        self.favorite_check.grid(row=6, column=1, sticky="w", padx=(0, 12), pady=4)

        self.created_at_label = ctk.CTkLabel(self.form)
        self.created_at_label.grid(row=7, column=0, sticky="w", padx=(12, 6), pady=4)
        self.created_at_value = ctk.CTkLabel(self.form, textvariable=self.created_at_var, anchor="w")
        self.created_at_value.grid(row=7, column=1, sticky="w", padx=(0, 12), pady=4)

        self.updated_at_label = ctk.CTkLabel(self.form)
        self.updated_at_label.grid(row=8, column=0, sticky="w", padx=(12, 6), pady=4)
        self.updated_at_value = ctk.CTkLabel(self.form, textvariable=self.updated_at_var, anchor="w")
        self.updated_at_value.grid(row=8, column=1, sticky="w", padx=(0, 12), pady=4)

        self.button_row = ctk.CTkFrame(self.form, fg_color="transparent")
        self.button_row.grid(row=9, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 12))
        for idx in range(3):
            self.button_row.grid_columnconfigure(idx, weight=1)

        self.add_button = ctk.CTkButton(self.button_row, command=self.add_note_and_new)
        self.add_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.save_button = ctk.CTkButton(self.button_row, command=self.save_note)
        self.save_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.delete_button = ctk.CTkButton(self.button_row, command=self.delete_note)
        self.delete_button.grid(row=0, column=2, padx=4, pady=4, sticky="ew")

        self.toggle_pinned_button = ctk.CTkButton(self.button_row, command=self.toggle_pinned)
        self.toggle_pinned_button.grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        self.toggle_favorite_button = ctk.CTkButton(self.button_row, command=self.toggle_favorite)
        self.toggle_favorite_button.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        self.clear_button = ctk.CTkButton(self.button_row, command=self.start_add_note)
        self.clear_button.grid(row=1, column=2, padx=4, pady=4, sticky="ew")

    @staticmethod
    def _format_date_only(raw: str) -> str:
        prepared = str(raw or "").strip()
        if not prepared:
            return ""
        try:
            return datetime.fromisoformat(prepared).strftime("%d/%m/%Y")
        except ValueError:
            pass
        try:
            return format_date(parse_date_flexible(prepared))
        except ValueError:
            return prepared

    @staticmethod
    def _content_preview(raw: str, limit: int = 90) -> str:
        preview = raw.replace("\n", " ").strip()
        if len(preview) <= limit:
            return preview
        return f"{preview[:limit]}..."

    def apply_translations(self) -> None:
        t = self.app.t
        self.query_label.configure(text=t("query"))
        self.tag_label.configure(text=t("tag"))
        self.filter_label.configure(text=t("filter"))
        self.sort_label.configure(text=t("sort"))
        self.search_button.configure(text=t("search"))
        self.reset_button.configure(text=t("reset"))

        self.list_title.configure(text=t("notes_list"))
        self.table.heading("title", text=t("title"))
        self.table.heading("content", text=t("content"))
        self.table.heading("tags", text=t("tags"))
        self.table.heading("created_date", text=t("created_date"))

        self.form_title.configure(text=t("note_form"))
        self.title_label.configure(text=t("title"))
        self.content_label.configure(text=t("content"))
        self.tags_label.configure(text=f"{t('tags')} (csv)")
        self.color_label.configure(text=t("color_label"))
        self.pinned_check.configure(text=t("pinned"))
        self.favorite_check.configure(text=t("favorite"))
        self.created_at_label.configure(text=t("created_at"))
        self.updated_at_label.configure(text=t("updated_at"))

        self.add_button.configure(text=t("add_note"))
        self.save_button.configure(text=t("save"))
        self.delete_button.configure(text=t("delete"))
        self.toggle_pinned_button.configure(text=t("toggle_pinned"))
        self.toggle_favorite_button.configure(text=t("toggle_favorite"))
        self.clear_button.configure(text=t("clear"))

        filter_options = [
            ("all", t("filter_all")),
            ("pinned", t("filter_pinned")),
            ("favorites", t("filter_favorites")),
        ]
        self._filter_map = {label: value for value, label in filter_options}
        filter_labels = [label for _, label in filter_options]
        self.filter_menu.configure(values=filter_labels)
        selected_filter = next(label for value, label in filter_options if value == self.filter_value)
        self.filter_var.set(selected_filter)

        sort_options = [
            ("updated", t("sort_updated")),
            ("created", t("sort_created")),
            ("title", t("sort_title")),
        ]
        self._sort_map = {label: value for value, label in sort_options}
        sort_labels = [label for _, label in sort_options]
        self.sort_menu.configure(values=sort_labels)
        selected_sort = next(label for value, label in sort_options if value == self.sort_value)
        self.sort_var.set(selected_sort)

    def refresh(self) -> None:
        notes = self.app.service.list_notes(
            query=self.query_var.get(),
            tag=self.tag_var.get(),
            filter_by=self.filter_value,
            sort_by=self.sort_value,
        )

        for item_id in self.table.get_children():
            self.table.delete(item_id)

        if not notes:
            self.table.insert("", "end", iid="empty", values=(self.app.t("no_notes"), "", "", ""))
            return

        for note in notes:
            self.table.insert(
                "",
                "end",
                iid=str(note.id),
                values=(
                    note.title,
                    self._content_preview(note.content),
                    ", ".join(note.tags) if note.tags else "-",
                    self._format_date_only(note.created_at),
                ),
            )

        if self.selected_note_id is not None:
            selected_iid = str(self.selected_note_id)
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
        self.sort_value = self._sort_map.get(self.sort_var.get(), "updated")
        self.refresh()

    def _reset_filters(self) -> None:
        self.query_var.set("")
        self.tag_var.set("")
        self.filter_value = "all"
        self.sort_value = "updated"
        self.apply_translations()
        self.refresh()

    def _fill_form(self, note_id: int) -> None:
        try:
            note = self.app.service.get_note(note_id)
        except ValueError:
            self.start_add_note()
            self.refresh()
            return

        self.selected_note_id = note.id

        self.title_var.set(note.title)
        self.tags_var.set(", ".join(note.tags))
        self.color_label_var.set(note.color_label)
        self.pinned_var.set(note.pinned)
        self.favorite_var.set(note.favorite)
        self.created_at_var.set(self._format_date_only(note.created_at))
        self.updated_at_var.set(self._format_date_only(note.updated_at))
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", note.content)



    def start_add_note(self) -> None:
        self.selected_note_id = None
        self.title_var.set("")
        self.tags_var.set("")
        self.color_label_var.set("default")
        self.pinned_var.set(False)
        self.favorite_var.set(False)
        self.created_at_var.set("")
        self.updated_at_var.set("")
        self.content_text.delete("1.0", "end")
        self._clear_table_selection()
        self.title_entry.focus_set()

    def _collect_form(self) -> dict:
        return {
            "title": self.title_var.get().strip(),
            "content": self.content_text.get("1.0", "end").strip(),
            "tags": split_csv(self.tags_var.get()),
            "pinned": self.pinned_var.get(),
            "favorite": self.favorite_var.get(),
            "color_label": self.color_label_var.get(),
        }

    @staticmethod
    def _normalize_tags_for_compare(tags: list[str]) -> list[str]:
        return sorted({item.strip().lower() for item in tags if item and item.strip()})

    def _payload_has_note_data(self, payload: dict) -> bool:
        return any(
            [
                payload["title"],
                payload["content"],
                payload["tags"],
                payload["pinned"],
                payload["favorite"],
                (payload["color_label"] or "default") != "default",
            ]
        )

    def _payload_differs_note(self, payload: dict, note) -> bool:
        if payload["title"] != note.title:
            return True
        if payload["content"] != note.content:
            return True
        if self._normalize_tags_for_compare(payload["tags"]) != self._normalize_tags_for_compare(note.tags):
            return True
        if bool(payload["pinned"]) != bool(note.pinned):
            return True
        if bool(payload["favorite"]) != bool(note.favorite):
            return True
        if (payload["color_label"] or "default") != (note.color_label or "default"):
            return True
        return False

    def _save_current_note_if_needed(self):
        payload = self._collect_form()

        if self.selected_note_id is None:
            if not self._payload_has_note_data(payload):
                return None
            return self.app.service.add_note(**payload)

        note = self.app.service.get_note(self.selected_note_id)
        if not self._payload_differs_note(payload, note):
            return None
        return self.app.service.update_note(note_id=self.selected_note_id, **payload)

    def add_note_and_new(self) -> None:
        try:
            note = self._save_current_note_if_needed()
            if note is not None:
                self.app.notify_status(f"{self.app.t('save')}: {note.title}")
            self.start_add_note()
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def save_note(self) -> None:
        try:
            payload = self._collect_form()
            if self.selected_note_id is None:
                note = self.app.service.add_note(**payload)
            else:
                note = self.app.service.update_note(note_id=self.selected_note_id, **payload)

            self.refresh()
            self.select_note(note.id)
            self.app.notify_status(f"{self.app.t('save')}: {note.title}")
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def delete_note(self) -> None:
        if self.selected_note_id is None:
            dialogs.show_info(self.app.t("info"), self.app.t("select_note_first"))
            return
        if not dialogs.ask_yes_no(self.app.t("info"), self.app.t("confirm_delete_note")):
            return
        try:
            self.app.service.delete_note(self.selected_note_id)
            self.start_add_note()
            self.refresh()
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def toggle_pinned(self) -> None:
        if self.selected_note_id is None:
            dialogs.show_info(self.app.t("info"), self.app.t("select_note_first"))
            return
        note = self.app.service.toggle_note_pinned(self.selected_note_id)
        self.refresh()
        self.select_note(note.id)

    def toggle_favorite(self) -> None:
        if self.selected_note_id is None:
            dialogs.show_info(self.app.t("info"), self.app.t("select_note_first"))
            return
        note = self.app.service.toggle_note_favorite(self.selected_note_id)
        self.refresh()
        self.select_note(note.id)

    def select_note(self, note_id: int) -> None:
        self.selected_note_id = note_id
        selected_iid = str(note_id)
        if selected_iid not in self.table.get_children():
            self.refresh()
            if selected_iid not in self.table.get_children():
                return
        self._set_table_selection(selected_iid)
        self._fill_form(note_id)

