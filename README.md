# Personal Assistant

Desktop (CustomTkinter) and CLI application for contacts and notes management.

## AI Maintainer Guide

For fast onboarding in future AI-assisted sessions, read:

- `AI_MAINTAINER_GUIDE.md`

## Implemented features

- Contacts: add, list, search, edit, delete.
- Contact fields: first_name, nickname, last_name, country, country_phone_code, phone_number, email, address, birthday, comment, favorite.
- Validation for contact fields (phone, birthday format DD/MM/YYYY, email).
- Upcoming birthdays for the next N days.
- Notes: add, list, search, edit, delete.
- Notes tags, pinned/favorite flags, created/updated timestamps.
- Global search across contacts and notes.
- Language switch (English / Українська).
- Data persistence in JSON with backward compatibility.
- Full CLI support remains available.

## Run from source

1. Install dependencies:

```powershell
python -m pip install --upgrade customtkinter
```

2. Start GUI:

```powershell
python gui.py
```

3. Start CLI:

```powershell
python main.py
```

If `python` is not in PATH, use an explicit interpreter path, for example:

```powershell
& "C:\Users\User\AppData\Local\Python\bin\python.exe" gui.py
```

## Data storage

Data is stored in:

- `~/.personal_assistant/data.json`

In CLI mode you can print the path with:

```text
data-path
```

## Build EXE (PyInstaller)

1. Install PyInstaller:

```powershell
python -m pip install --upgrade pyinstaller
```

2. Build GUI EXE (one-folder):

```powershell
python -m PyInstaller --noconfirm --clean --windowed --name PersonalAssistant gui.py
```

Result:

- `dist\PersonalAssistant\PersonalAssistant.exe`

Important workflow rules:
- After any code change, always attempt EXE rebuild immediately.
- Always build test output to `dist_temp`.
- Only after user confirmation, promote test build from `dist_temp` to release `dist`.
- Before replacing release build, create backup of previous release folder in `dist`.

Recommended safe build command (same drive as source):

```powershell
python -m PyInstaller --noconfirm --windowed --name PersonalAssistant --distpath ".\dist_temp" --workpath ".\build_temp" --specpath "." gui.py
```

Promotion command (after user confirms test build):

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
if (Test-Path ".\dist\PersonalAssistant") { Move-Item ".\dist\PersonalAssistant" ".\dist\PersonalAssistant_backup_$ts" }
Copy-Item ".\dist_temp\PersonalAssistant" ".\dist\PersonalAssistant" -Recurse -Force
```

## Build installer (Setup.exe)

Use Inno Setup to create an installable package.

1. Install Inno Setup.
2. Open `installer.iss` from this repository.
3. Build the installer in Inno Setup.

Result:

- `Output\PersonalAssistantSetup.exe`
