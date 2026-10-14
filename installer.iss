#ifndef MyAppVersion
#define MyAppVersion "1.3.26"
#endif
#define MyAppName "Mistus Copy Pasta"
#define MyAppPublisher "Mistus Project"
#define MyAppURL "https://github.com/mistu01/copypastapro"
#define MyAppExeName "MistusCopyPasta.exe"

[Setup]
AppId={{9FA1A945-8C17-48DF-9F52-3298C512F981}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; 64-bit mode: ensures installation into "Program Files" instead of "Program Files (x86)" on 64-bit Windows
ArchitecturesInstallIn64BitMode=x64compatible

; Destination: Program Files with admin privilege, or fallback
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputBaseFilename=Mistus_Copy_Pasta_Setup_v{#MyAppVersion}
OutputDir=.
SetupIconFile=app_icon.ico

; Visuals & Branding
WizardStyle=modern
WizardImageFile=wizard_large.bmp
WizardSmallImageFile=wizard_small.bmp

; Pages configuration: clean streamlined installer
DisableWelcomePage=no
LicenseFile=LICENSE.txt
DisableDirPage=no
DisableProgramGroupPage=no
DisableReadyPage=no
DisableFinishedPage=no
AlwaysShowDirOnReadyPage=yes
AlwaysShowGroupOnReadyPage=yes

; Permissions & System integration
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\app_icon.ico
UninstallDisplayName={#MyAppName} (Clipboard Manager & 2FA)
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}

; Compression
Compression=lzma2/max
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Launch {#MyAppName} automatically when Windows starts"; GroupDescription: "System Startup:"

[Files]
Source: "dist\MistusCopyPasta\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Comment: "{#MyAppName} Clipboard Manager & 2FA"
Name: "{group}\Documentation"; Filename: "{app}\README.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon
; Windows Startup folder
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: startupicon

[Registry]
; Register App Path so CopyPasta can be launched from Win+R Run dialog
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletekey
; App Info
Root: HKCU; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.bmp"

[Code]
function PostMessage(hWnd: HWND; Msg: Cardinal; wParam: LongInt; lParam: LongInt): Boolean;
external 'PostMessageW@user32.dll stdcall';

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DisabledHotkeys: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    // 1. Re-enable native Windows 10/11 Clipboard History
    RegWriteDWordValue(HKCU, 'Software\Microsoft\Clipboard', 'EnableClipboardHistory', 1);

    // 2. Remove 'V' from DisabledHotkeys in Explorer\Advanced so Win+V works natively
    if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', 'DisabledHotkeys', DisabledHotkeys) then
    begin
      StringChangeEx(DisabledHotkeys, 'V', '', True);
      if Length(DisabledHotkeys) > 0 then
        RegWriteStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', 'DisabledHotkeys', DisabledHotkeys)
      else
        RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', 'DisabledHotkeys');
    end;

    // 3. Broadcast WM_SETTINGCHANGE so Windows Explorer reloads hotkeys immediately
    // HWND_BROADCAST = 65535 ($FFFF), WM_SETTINGCHANGE = 26 ($001A)
    try
      PostMessage(65535, 26, 0, 0);
    except
      // Ignore if broadcast fails
    end;
  end;
end;
