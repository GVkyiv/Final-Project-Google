#define MyAppName "Personal Assistant"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Neoversity"
#define MyAppExeName "PersonalAssistant.exe"

[Setup]
AppId={{7CB9D7E7-9F8C-4A73-B6CF-5E65E5A2A241}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
OutputDir=Output
OutputBaseFilename=Personal Assistant.setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=yes
Uninstallable=no
CreateUninstallRegKey=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\PersonalAssistant\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
