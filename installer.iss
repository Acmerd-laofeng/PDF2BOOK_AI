; -*- encoding: utf-8 -*-
; PDF2BOOK AI v4.0 - Inno Setup 安装包脚本
; 使用 ISCC 编译生成 PDF2BOOK_AI_Setup_v4.0.exe

#define MyAppName "PDF2BOOK AI"
#define MyAppVersion "4.0.7"
#define MyAppPublisher "ACMERD"
#define MyAppURL "https://acmerd.com"
#define MyAppExeName "PDF2BOOK_AI.exe"
#define MyAppDescription "AI 智能电子书重构平台"

; 源文件路径（PyInstaller 打包产物）
#define BuildOutputDir "dist"

[Setup]
; 基本信息息
AppId={{8A3F7E2D-1B5C-4D6E-9F8A-2B3C4D5E6F7A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (c) 2026 ACMERD
AppContact=acmerd.com
AppComments={#MyAppDescription}

; 版本信息
VersionInfoVersion=4.0.7.0
VersionInfoCompany=ACMERD
VersionInfoDescription={#MyAppDescription}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=4.0.7.0

; 安装设置
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; 输出设置
OutputDir=installer_output
OutputBaseFilename=PDF2BOOK_AI_Setup
Compression=lzma2/ultra
SolidCompression=yes
LZMANumBlockThreads=4
WizardStyle=modern

; 图标和横幅
SetupIconFile=resources\icon.ico
WizardImageFile=resources\installer_banner.bmp
WizardSmallImageFile=resources\installer_small.bmp

; 卸载设置
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; 语言
ShowLanguageDialog=auto
LanguageDetectionMethod=uilanguage

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
; 中文自定义文本
chinesesimp.WelcomeLabel1=欢迎使用 {#MyAppName}
chinesesimp.WelcomeLabel2=这将把 {#MyAppName} v{#MyAppVersion} 安装到您的计算机上。%n%n{#MyAppDescription} — 从扫描 PDF 到精美 EPUB，AI 驱动的智能转换。%n%n建议关闭其他应用程序后继续。
chinesesimp.FinishedHeading=安装完成！
chinesesimp.FinishedLabel={#MyAppName} 已成功安装到您的计算机上。%n%n点击"完成"退出安装程序。
chinesesimp.RunAfter=立即启动 {#MyAppName}
chinesesimp.ViewReadme=查看 README

; 英文
english.WelcomeLabel1=Welcome to {#MyAppName}
english.WelcomeLabel2=This will install {#MyAppName} v{#MyAppVersion} on your computer.%n%n{#MyAppDescription} - Transform scanned PDFs into polished EPUBs with AI.%n%nIt is recommended that you close all other applications before continuing.
english.FinishedHeading=Installation Complete!
english.FinishedLabel={#MyAppName} has been successfully installed on your computer.%n%nClick Finish to exit the installer.
english.RunAfter=Launch {#MyAppName} now
english.ViewReadme=View README

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "associatepdf"; Description: "关联 .pdf 文件（右键打开）"; GroupDescription: "其他选项:"; Flags: unchecked

[Files]
; 主程序
Source: "{#BuildOutputDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: nocompression
; README（不默认勾选查看）
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 开始菜单
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} 帮助"; Filename: "{app}\README.md"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
; 桌面
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"


[Registry]
; PDF 右键打开（可选任务）
Root: HKCU; Subkey: "Software\Classes\.pdf\shell\{#MyAppName}"; ValueType: string; ValueName: ""; ValueData: "用 {#MyAppName} 打开"; Flags: uninsdeletekey; Tasks: associatepdf
Root: HKCU; Subkey: "Software\Classes\.pdf\shell\{#MyAppName}\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: associatepdf

[Run]
; 安装后运行
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:RunAfter}"; Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallDelete]
Type: filesandordirs; Name: "{app}\cache"
Type: filesandordirs; Name: "{app}\database"
Type: filesandordirs; Name: "{app}"

[Code]
// 自定义代码
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
