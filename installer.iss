[Setup]
AppName=Vocalix
AppVersion=1.0.0
AppPublisher=Vocalix
AppPublisherURL=https://github.com/akkshattshah/vocalix
DefaultDirName={autopf}\Vocalix
DefaultGroupName=Vocalix
UninstallDisplayIcon={app}\Vocalix.exe
OutputBaseFilename=Vocalix-V1-Setup
OutputDir=.
Compression=lzma2
SolidCompression=yes
SetupIconFile=icon.ico
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
Source: "dist\Vocalix\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Vocalix"; Filename: "{app}\Vocalix.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\Vocalix"; Filename: "{app}\Vocalix.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Vocalix"; ValueData: """{app}\Vocalix.exe"""; Flags: uninsdeletevalue

[Run]
Filename: "{app}\Vocalix.exe"; Description: "Launch Vocalix"; Flags: nowait postinstall skipifsilent
