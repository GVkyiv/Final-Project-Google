from __future__ import annotations

import os
import subprocess
from pathlib import Path
import tkinter as tk

import customtkinter as ctk

from . import dialogs


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app) -> None:
        super().__init__(parent)
        self.app = app

        self.data_path_var = tk.StringVar()
        self.density_var = tk.StringVar()
        self.appearance_var = tk.StringVar()

        self._density_map: dict[str, str] = {}
        self._appearance_map: dict[str, str] = {}
        self._updating_options = False

        self.grid_columnconfigure(0, weight=1)

        self._build_layout()
        self.apply_translations()
        self.refresh()

    def _build_layout(self) -> None:
        pad = self.app.ui_tokens.outer_pad
        gap = self.app.ui_tokens.section_gap

        self.panel = ctk.CTkFrame(self, corner_radius=self.app.ui_tokens.corner_radius)
        self.panel.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)
        self.panel.grid_columnconfigure(1, weight=1)

        self.data_path_label = ctk.CTkLabel(self.panel, anchor="w")
        self.data_path_label.grid(row=0, column=0, sticky="w", padx=(12, 6), pady=(12, 4))

        self.data_path_entry = ctk.CTkEntry(self.panel, textvariable=self.data_path_var, state="disabled")
        self.data_path_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(12, 4))

        self.open_folder_button = ctk.CTkButton(self.panel, command=self._open_data_folder)
        self.open_folder_button.grid(row=1, column=0, sticky="w", padx=12, pady=4)

        self.change_path_button = ctk.CTkButton(self.panel, command=self._change_data_path)
        self.change_path_button.grid(row=1, column=1, sticky="w", padx=(0, 12), pady=4)

        self.export_button = ctk.CTkButton(self.panel, command=self._export_json)
        self.export_button.grid(row=2, column=0, sticky="w", padx=12, pady=4)

        self.import_button = ctk.CTkButton(self.panel, command=self._import_json)
        self.import_button.grid(row=2, column=1, sticky="w", padx=(0, 12), pady=4)

        self.backup_button = ctk.CTkButton(self.panel, command=self._create_backup)
        self.backup_button.grid(row=3, column=0, sticky="w", padx=12, pady=4)

        self.density_label = ctk.CTkLabel(self.panel, anchor="w")
        self.density_label.grid(row=4, column=0, sticky="w", padx=(12, 6), pady=(10, 4))

        self.density_menu = ctk.CTkOptionMenu(
            self.panel,
            variable=self.density_var,
            values=[],
            command=self._on_density_changed,
        )
        self.density_menu.grid(row=4, column=1, sticky="w", padx=(0, 12), pady=(10, 4))

        self.appearance_label = ctk.CTkLabel(self.panel, anchor="w")
        self.appearance_label.grid(row=5, column=0, sticky="w", padx=(12, 6), pady=(4, 12))

        self.appearance_menu = ctk.CTkOptionMenu(
            self.panel,
            variable=self.appearance_var,
            values=[],
            command=self._on_appearance_changed,
        )
        self.appearance_menu.grid(row=5, column=1, sticky="w", padx=(0, 12), pady=(4, 12))

    def apply_translations(self) -> None:
        t = self.app.t
        self.data_path_label.configure(text=t("data_path"))
        self.open_folder_button.configure(text=t("open_data_folder"))
        self.change_path_button.configure(text=t("change_data_file"))
        self.export_button.configure(text=t("export_json"))
        self.import_button.configure(text=t("import_json"))
        self.backup_button.configure(text=t("create_backup"))
        self.density_label.configure(text=t("ui_density"))
        self.appearance_label.configure(text=t("appearance_mode"))

        density_options = [("compact", t("compact")), ("normal", t("normal"))]
        self._density_map = {label: value for value, label in density_options}
        density_labels = [label for _, label in density_options]

        appearance_options = [
            ("system", t("theme_system")),
            ("light", t("theme_light")),
            ("dark", t("theme_dark")),
        ]
        self._appearance_map = {label: value for value, label in appearance_options}
        appearance_labels = [label for _, label in appearance_options]

        self._updating_options = True
        self.density_menu.configure(values=density_labels)
        self.appearance_menu.configure(values=appearance_labels)

        current_density = self.app.service.settings.ui_density
        current_density_label = next(label for value, label in density_options if value == current_density)
        self.density_var.set(current_density_label)

        current_mode = getattr(self.app.service.settings, "appearance_mode", "system")
        current_mode_label = next(label for value, label in appearance_options if value == current_mode)
        self.appearance_var.set(current_mode_label)
        self._updating_options = False

    def refresh(self) -> None:
        self.data_path_var.set(str(self.app.service.get_data_path()))

    def _open_data_folder(self) -> None:
        folder = self.app.service.get_data_folder()
        try:
            if os.name == "nt":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif os.name == "posix":
                subprocess.Popen(["xdg-open", str(folder)])
            else:
                dialogs.show_info(self.app.t("info"), str(folder))
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def _change_data_path(self) -> None:
        path = dialogs.ask_data_path(self.app.service.get_data_folder())
        if not path:
            return
        try:
            self.app.service.set_data_path(Path(path))
            self.refresh()
            self.app.refresh_all()
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def _export_json(self) -> None:
        path = dialogs.ask_export_path(self.app.service.get_data_folder())
        if not path:
            return
        try:
            self.app.service.export_json(Path(path))
            dialogs.show_info(self.app.t("info"), self.app.t("export_done"))
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def _import_json(self) -> None:
        path = dialogs.ask_import_path(self.app.service.get_data_folder())
        if not path:
            return
        try:
            self.app.service.import_json(Path(path))
            self.refresh()
            self.app.refresh_all()
            dialogs.show_info(self.app.t("info"), self.app.t("import_done"))
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def _create_backup(self) -> None:
        try:
            backup = self.app.service.create_backup()
            dialogs.show_info(self.app.t("info"), f"{self.app.t('backup_created')} {backup}")
        except Exception as exc:  # pragma: no cover - GUI runtime
            dialogs.show_error(self.app.t("error"), str(exc))

    def _on_density_changed(self, _value: str | None = None) -> None:
        if self._updating_options:
            return
        value = self._density_map.get(self.density_var.get())
        if not value:
            return
        self.app.set_density(value)

    def _on_appearance_changed(self, _value: str | None = None) -> None:
        if self._updating_options:
            return
        value = self._appearance_map.get(self.appearance_var.get())
        if not value:
            return
        self.app.set_appearance_mode(value)
