[Setup]
AppName=NOLT Office Assistant
AppVersion=1.0.0
DefaultDirName={autopf}\NOLT Office Assistant
DefaultGroupName=NOLT Office Assistant
UninstallDisplayIcon={app}\NOLT_OA_1.0.0v.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=NOLT_OA_1.0.0v_Setup
SetupIconFile=favicon.ico
PrivilegesRequired=lowest

[Files]
Source: "dist\NOLT_OA_1.0.0v.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\NOLT Office Assistant"; Filename: "{app}\NOLT_OA_1.0.0v.exe"
Name: "{autodesktop}\NOLT Office Assistant"; Filename: "{app}\NOLT_OA_1.0.0v.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"
