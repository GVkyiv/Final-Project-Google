from pathlib import Path

from .storage import JsonStorage


class SettingsService:
    def __init__(self, storage: JsonStorage, facade) -> None:
        self.storage = storage
        self.facade = facade
        self.settings = facade.settings

    def _persist_settings(self) -> None:
        self.storage.save_settings(self.settings)

    def set_language(self, language: str) -> None:
        if language not in {"en", "uk"}:
            raise ValueError("Unsupported language")
        self.settings.language = language
        self._persist_settings()

    def set_ui_density(self, density: str) -> None:
        if density not in {"compact", "normal"}:
            raise ValueError("Unsupported UI density")
        self.settings.ui_density = density
        self._persist_settings()

    def set_appearance_mode(self, mode: str) -> None:
        if mode not in {"light", "dark", "system"}:
            raise ValueError("Unsupported appearance mode")
        self.settings.appearance_mode = mode
        self._persist_settings()

    def set_data_path(self, path: Path) -> None:
        resolved = path.expanduser()
        if resolved.suffix.lower() != ".json":
            raise ValueError("Data file should have .json extension")

        if resolved.exists():
            # load external data
            try:
                new_data = self.storage.load_data(resolved)
                self.facade.data = new_data
            except Exception as e:
                raise ValueError(f"Failed to load data from path: {e}")

        self.settings.data_path = str(resolved)
        self.facade.data_path = resolved
        self._persist_settings()
        self.facade._autosave()
