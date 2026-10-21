#define AppName "PCULTIMATE"
#define AppVersion "0.2.0"
[Setup]
AppId={{A7D25C2A-948B-48D4-BAF7-CF314F98F10A}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\PCULTIMATE
DefaultGroupName=PCULTIMATE
OutputDir=dist
OutputBaseFilename=PCULTIMATE-Setup
SetupIconFile=assets\pcultimate.ico
UninstallDisplayIcon={app}\PCULTIMATE.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
[Files]
Source: "dist\PCULTIMATE.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\PCULTIMATE"; Filename: "{app}\PCULTIMATE.exe"
Name: "{autodesktop}\PCULTIMATE"; Filename: "{app}\PCULTIMATE.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
[Run]
Filename: "{app}\PCULTIMATE.exe"; Description: "Launch PCULTIMATE"; Flags: nowait postinstall skipifsilent
