import PyInstaller.__main__

options = [
    'gui.py',
    '--noconfirm',
    '--name', 'PersonalAssistantDemo',
    '--add-data', 'app/theme.json;app',
    '--collect-all', 'customtkinter'
]

PyInstaller.__main__.run(options)
