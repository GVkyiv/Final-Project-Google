from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox


def ask_export_path(initial_dir: Path) -> str:
    return filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        initialdir=str(initial_dir),
        title="Export JSON",
    )


def ask_import_path(initial_dir: Path) -> str:
    return filedialog.askopenfilename(
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        initialdir=str(initial_dir),
        title="Import JSON",
    )


def ask_data_path(initial_dir: Path) -> str:
    return filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        initialdir=str(initial_dir),
        title="Select data.json path",
    )


def show_error(title: str, text: str) -> None:
    messagebox.showerror(title, text)


def show_info(title: str, text: str) -> None:
    messagebox.showinfo(title, text)


def ask_yes_no(title: str, text: str) -> bool:
    return messagebox.askyesno(title, text)
