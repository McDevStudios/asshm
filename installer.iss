#define MyAppName "ASSHM"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "McDevStudios"
#define MyAppURL "https://github.com/McDevStudios/asshm"
#define MyAppExeName "asshm.exe"

[Setup]
AppId={{5A8E2F94-3C35-4F72-B0F8-C9C5E53B76E9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=build
OutputBaseFilename=asshm
SetupIconFile=src\assets\ASSHM.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; ASSHM Application Files
Source: "build\asshm\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

; Bundled Installers
Source: "build\installers\python-3.13.2-amd64.exe"; DestDir: "{app}\installers"; Flags: ignoreversion
Source: "build\installers\putty-64bit-0.79-installer.msi"; DestDir: "{app}\installers"; Flags: ignoreversion
Source: "build\installers\WinSCP-6.3.7-Setup.exe"; DestDir: "{app}\installers"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Step 1/3 - Install Python
Filename: "{app}\installers\python-3.13.2-amd64.exe"; \
    Parameters: "/custom InstallAllUsers=1 PrependPath=1 Include_test=0 Include_launcher=1"; \
    StatusMsg: "Step 1/3: Installing Python..."; \
    Flags: waituntilterminated shellexec

; Step 2/3 - Install PuTTY via MSI
Filename: "msiexec.exe"; \
    Parameters: "/i ""{app}\installers\putty-64bit-0.79-installer.msi"" /qb! ALLUSERS=1 /l*v ""{app}\putty_install.log"""; \
    StatusMsg: "Step 2/3: Installing PuTTY..."; \
    Flags: waituntilterminated

; Step 3/3 - Install WinSCP
Filename: "{app}\installers\WinSCP-6.3.7-Setup.exe"; \
    Parameters: "/LOADINF=""{tmp}\winscp.inf"" /NORESTART /ALLUSERS /NORUN /NOTOUR"; \
    StatusMsg: "Step 3/3: Installing WinSCP..."; \
    Flags: waituntilterminated

; Launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure InitializeWizard;
begin
  // Create WinSCP INF file for visible installation
  SaveStringToFile(ExpandConstant('{tmp}\winscp.inf'),
    '[Setup]' + #13#10 +
    'ShowInstDetails=1' + #13#10 +
    'ShowUninstDetails=1' + #13#10 +
    'Setup Type=Custom' + #13#10 +
    'DisableFinishedPage=0' + #13#10, False);
end;

[Messages]
; Custom status messages for installation steps
StatusInstallingLabel=Installing components... %1 