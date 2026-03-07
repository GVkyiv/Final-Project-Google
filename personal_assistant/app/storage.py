from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

from .models import AppData, AppSettings


class JsonStorage:
    def __init__(self, base_dir: Path | None = None, settings_path: Path | None = None) -> None:
        self.base_dir = base_dir or (Path.home() / ".personal_assistant")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = settings_path or (self.base_dir / "settings.json")

    @staticmethod
    def _corrupted_backup_path(path: Path) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return path.with_name(f"{path.stem}.corrupted_{stamp}{path.suffix}")

    def _move_as_corrupted(self, path: Path) -> None:
        if not path.exists():
            return
        backup = self._corrupted_backup_path(path)
        try:
            path.replace(backup)
        except OSError:
            # If backup rename fails (permissions/locks), keep the original file and fall back to defaults.
            return

    def _read_json_object(self, path: Path, *, fallback: Dict[str, object]) -> Dict[str, object]:
        if not path.exists():
            return dict(fallback)

        try:
            text = path.read_text(encoding="utf-8")
            raw = json.loads(text)
        except (OSError, json.JSONDecodeError):
            self._move_as_corrupted(path)
            return dict(fallback)

        if not isinstance(raw, dict):
            self._move_as_corrupted(path)
            return dict(fallback)

        return raw

    @staticmethod
    def _write_json_atomic(path: Path, payload: Dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        json_text = json.dumps(payload, ensure_ascii=False, indent=2)

        temp_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                delete=False,
                dir=path.parent,
                prefix=f"{path.stem}.",
                suffix=".tmp",
            ) as temp_file:
                temp_file.write(json_text)
                temp_file.flush()
                temp_path = Path(temp_file.name)

            temp_path.replace(path)
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def load_settings(self) -> AppSettings:
        raw = self._read_json_object(self.settings_path, fallback={})
        return AppSettings.from_raw(raw)

    def save_settings(self, settings: AppSettings) -> None:
        self._write_json_atomic(self.settings_path, settings.to_raw())

    def resolve_data_path(self, settings: AppSettings) -> Path:
        if settings.data_path:
            return Path(settings.data_path).expanduser()
        return self.base_dir / "data.json"

    def load_data(self, data_path: Path) -> AppData:
        raw = self._read_json_object(data_path, fallback={})
        return AppData.from_raw(raw)

    def save_data(self, data: AppData, data_path: Path) -> None:
        self._write_json_atomic(data_path, data.to_raw())

    def export_json(self, data: AppData, destination: Path) -> None:
        self._write_json_atomic(destination, data.to_raw())

    def import_json(self, source: Path) -> AppData:
        if not source.exists():
            raise ValueError(f"File does not exist: {source}")
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in file: {source}") from exc
        if not isinstance(raw, dict):
            raise ValueError("Imported JSON root must be an object.")
        return AppData.from_raw(raw)

    def create_backup(self, data: AppData, data_path: Path) -> Path:
        backup_dir = data_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"data_backup_{stamp}.json"
        self.export_json(data, backup_path)
        return backup_path