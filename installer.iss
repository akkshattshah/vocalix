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
SetupIconFile=
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
Source: "dist\Vocalix\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Vocalix"; Filename: "{app}\Vocalix.exe"
Name: "{autodesktop}\Vocalix"; Filename: "{app}\Vocalix.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\Vocalix.exe"; Description: "Launch Vocalix"; Flags: nowait postinstall skipifsilent
