# AI Maintainer Guide (Personal Assistant)

This file is for future AI/code assistants that continue this project.
Goal: understand architecture quickly and make safe changes without breaking JSON compatibility, GUI, or CLI.

## 1) What this project is

Personal Assistant with two interfaces:
- GUI (Tkinter)
- CLI (cmd-based shell)

Main domains:
- Contacts
- Notes
- Birthdays (derived from contacts)
- Search (contacts + notes)
- Settings (language, density, data file)

## 2) Entry points

- GUI launcher: `gui.py` -> `personal_assistant.gui.main()` -> `AppWindow`
- CLI launcher: `main.py` -> `personal_assistant.main.main()` -> `AssistantCLI`

## 3) High-level architecture

Layered structure:
- `personal_assistant/app/` = domain + service + storage + validation + i18n
- `personal_assistant/ui/` = Tkinter views (pages)

Core flow:
1. UI/CLI calls `PersonalAssistantService`
2. Service validates + mutates in-memory `AppData`
3. Service autosaves via `JsonStorage`
4. JSON load/save goes through `AppData.from_raw()` / `to_raw()`

## 4) Important files and responsibilities

- `personal_assistant/app/models.py`
  - Dataclasses: `Contact`, `Note`, `AppSettings`, `AppData`
  - JSON migration compatibility is centralized here (especially `Contact.from_dict`)
  - Contact legacy compatibility properties: `name`, `phones`

- `personal_assistant/app/services.py`
  - Main application API for both GUI and CLI
  - Contact/Note CRUD, search, sorting, birthdays, dashboard summary
  - Country phone code dictionary: `COUNTRY_PHONE_CODES`

- `personal_assistant/app/storage.py`
  - JSON persistence and import/export/backup

- `personal_assistant/app/utils.py`
  - Date parsing/formatting (`DD/MM/YYYY` primary + legacy parsers)
  - Common normalization helpers

- `personal_assistant/app/validators.py`
  - Input validation for birthday/email/phone/code/required

- `personal_assistant/app/translations.py`
  - All UI i18n keys (`en`, `uk`)

- `personal_assistant/ui/*.py`
  - Tkinter pages (contacts, notes, birthdays, dashboard, search, settings)

- `personal_assistant/main.py`
  - CLI commands and argument parsing

## 5) Current Contact data contract (critical)

`Contact` fields:
- `id`
- `first_name`
- `nickname`
- `last_name`
- `country`
- `country_phone_code`
- `phone_number`
- `email`
- `address`
- `birthday` (string in `DD/MM/YYYY`)
- `comment`
- `favorite`
- `created_at`
- `updated_at`

Phone display (read model/service helpers):
- Combined UI/CLI display: `+code number` when both exist

## 6) JSON compatibility rules (must not break)

Implemented in `Contact.from_dict`:
- Old `name` -> new `first_name`
- Old `phones`/`phone` -> migrated into `phone_number` (+ code if reliably parsed)
- Missing new fields default to empty values
- Legacy birthday formats are normalized to `DD/MM/YYYY` when possible

Do not bypass `AppData.from_raw()` when loading JSON.

## 7) Validation contract (critical)

- Birthday: strict `DD/MM/YYYY`
- Country phone code: `+` + digits (`+123`)
- Phone number: allows digits/spaces/`-`/parentheses on input; normalized to digits
- If country is set and code is empty: service auto-fills code from country map

Main validators live in `validators.py`; call through service methods.

## 8) GUI map and where to modify what

- `ui/contacts_view.py`
  - Contact table columns, contact form fields, localized error mapping, localized country names, birthday auto-format (DD/MM/YYYY), add/update/delete UI actions

- `ui/birthdays_view.py`
  - Birthdays table (first/last/phone/email/birthday/days left)

- `ui/dashboard_view.py`
  - Stats + upcoming birthdays block + pinned/recent lists

- `ui/notes_view.py`
  - Notes table includes visible `created_at` and `updated_at`

- `ui/search_view.py`
  - Combined search results for contacts and notes

If you add a new displayed field:
1. Extend model/dataclass
2. Extend service list/search/sort if needed
3. Add translation keys
4. Update corresponding Treeview columns and form widgets
5. Verify JSON migration defaults

## 9) CLI behavior notes

CLI supports legacy contact style and newer fields in add flow.
Do not remove legacy options without migration path.
Primary CLI file: `personal_assistant/main.py`.

## 10) Date format policy

User-facing date format is `DD/MM/YYYY`.
Use utility functions from `utils.py`:
- `parse_date()` for strict format
- `parse_date_flexible()` for migration/legacy reads
- `format_date()` for rendering

## 11) Safe change checklist

Before finishing any feature:
1. Confirm UI still opens pages (`dashboard`, `contacts`, `notes`, `birthdays`, `search`, `settings`)
2. Add/edit/delete contact works
3. Birthday filtering/upcoming list works
4. Note add/edit/delete works and created_at is visible
5. JSON export/import/backup works
6. Old JSON still loads (no crash on missing new fields)
7. CLI basic commands still run
8. Run syntax check:
   - `python -m py_compile personal_assistant/app/*.py personal_assistant/ui/*.py personal_assistant/main.py`
9. Mandatory: after code changes, always attempt EXE rebuild via PyInstaller.
10. Build output policy:
   - Always build test EXE to `./dist_temp/PersonalAssistant/PersonalAssistant.exe` (never directly to release `dist`).
   - Treat `dist_temp` as test channel until user explicitly confirms it is OK.
11. Promotion policy after user confirmation:
   - Copy `dist_temp/PersonalAssistant` to `dist/PersonalAssistant`.
   - Before overwrite, move old `dist/PersonalAssistant` to timestamped backup: `dist/PersonalAssistant_backup_YYYYMMDD_HHMMSS`.
12. Recommended safe build command (same drive as source, avoids C:/D: specpath errors):
   - `python -m PyInstaller --noconfirm --windowed --name PersonalAssistant --distpath .\dist_temp --workpath .\build_temp --specpath . gui.py`

## 12) Known context for future maintainers

- `README.md` may lag behind current data model details; trust code in `models.py` + `services.py` first.
- When uncertain about expected behavior, prefer backward-compatible changes and defaults.

## 13) Change recipes (quick)

### Add new Contact field
1. Add field to `Contact` dataclass
2. Handle fallback/default in `Contact.from_dict`
3. Include field in UI form/table
4. Update service add/update/list/search/sort logic
5. Add i18n keys in `translations.py`
6. Verify import of old JSON and no crashes

### Add new Notes column
1. Update `Note` dataclass if needed
2. Update notes service methods
3. Add Treeview column in `notes_view.py`
4. Add translation key(s)

### Change phone normalization
1. Update `validators.py` (`validate_phone_number`, maybe `validate_phone`)
2. Review migration helpers in `models.py` and `services.py`
3. Re-check search and display methods in service/UI

---
If you are an AI assistant in a new chat, start from:
1. `personal_assistant/app/models.py`
2. `personal_assistant/app/services.py`
3. `personal_assistant/ui/app_window.py`
Then open the specific view/file for the requested feature.


