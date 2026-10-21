; Script de Instalación Profesional para Spotlight Music
; Compatible con Inno Setup 6.x

#define MyAppName "Spotlight Music"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Emerson Madrid"
#define MyAppURL "https://github.com/emersonmadrid/spotlight-music"
#define MyAppExeName "SpotlightMusic.exe"

[Setup]
AppId={{5D9E2F1B-4A73-4C3D-8B6A-91E5B70C8C31}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DisableProgramGroupPage=yes
DefaultGroupName={#MyAppName}
OutputDir=..\dist_installer
OutputBaseFilename=SpotlightMusic_Setup
SetupIconFile=..\spotlight.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Iniciar minimizado en la bandeja al arrancar Windows"; GroupDescription: "Opciones avanzadas:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\spotlight.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\spotlight.png"; DestDir: "{app}"; Flags: ignoreversion
; Motor de audio interno aislado en subcarpeta engine (cero archivos sueltos para el usuario)
Source: "..\dist\engine\*"; DestDir: "{app}\engine"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\DISCLAIMER.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\spotlight.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\spotlight.ico"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--tray"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
