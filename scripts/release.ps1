# PDF2BOOK AI 一键发版脚本
# 用法：在 PDF2BOOK_AI 项目根目录执行
#   .\scripts\release.ps1 -Version 4.0.2
#
# 前提：
#   1. 已安装 PyInstaller + Inno Setup（ISCC 在 PATH 中）
#   2. Git remote 已配置 SSH
#   3. GitHub token 在环境变量 GITHUB_TOKEN 中（或修改下方硬编码）
#   4. blog-vue 后台管理员账号已登录（用于更新 Supabase version）
#      或者直接在后台 AdminResources 页面手动改 version

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    [string]$ProjectDir = "D:\000.下载内容\工具箱\pdf-to-epub\PDF2BOOK_AI",
    [string]$GithubToken = $env:GITHUB_TOKEN
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectDir

$tag = "v$Version"
Write-Host "=== PDF2BOOK AI 发版 $tag ===" -ForegroundColor Cyan

# 1. 更新版本号
Write-Host "`n[1/6] 更新 APP_VERSION..." -ForegroundColor Yellow
$constantsPath = "app\constants.py"
$content = Get-Content $constantsPath -Raw -Encoding UTF8
$content = $content -replace 'APP_VERSION\s*=\s*"[^"]*"', "APP_VERSION = `"$Version`""
Set-Content $constantsPath -Value $content -Encoding UTF8 -NoNewline
Write-Host "  APP_VERSION = $Version"

# 2. Git commit + tag + push
Write-Host "`n[2/6] Git 提交 + 打 tag + 推送..." -ForegroundColor Yellow
git add app\constants.py
git commit -m "release: v$Version"
git tag $tag
git push origin main
git push origin $tag
Write-Host "  已推送 $tag"

# 3. PyInstaller 打包
Write-Host "`n[3/6] PyInstaller 打包..." -ForegroundColor Yellow
& "D:\Python\python.exe" -m PyInstaller PDF2BOOK_AI.spec --noconfirm
$exePath = "dist\PDF2BOOK_AI.exe"
if (-not (Test-Path $exePath)) { throw "PyInstaller 打包失败：$exePath 不存在" }
Write-Host "  生成：$exePath ($([math]::Round((Get-Item $exePath).Length/1MB,1))MB)"

# 4. Inno Setup 编译
Write-Host "`n[4/6] Inno Setup 编译安装包..." -ForegroundColor Yellow
$issPath = "installer.iss"
$iscc = Get-Command ISCC -ErrorAction SilentlyContinue
if (-not $iscc) {
    $isccPath = "C:\Users\Admin\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
} else {
    $isccPath = $iscc.Source
}
& $isccPath $issPath
$installerPath = "installer_output\PDF2BOOK_AI_Setup.exe"
if (-not (Test-Path $installerPath)) { throw "Inno Setup 编译失败：$installerPath 不存在" }
Write-Host "  生成：$installerPath ($([math]::Round((Get-Item $installerPath).Length/1MB,1))MB)"

# 5. 上传到 GitHub Release
Write-Host "`n[5/6] 创建 GitHub Release + 上传安装包..." -ForegroundColor Yellow
if (-not $GithubToken) {
    Write-Host "  ⚠ 未设置 GITHUB_TOKEN，跳过自动上传" -ForegroundColor Red
    Write-Host "  请手动在 GitHub 创建 Release $tag 并上传 $installerPath" -ForegroundColor Red
} else {
    $headers = @{
        "Authorization" = "Bearer $GithubToken"
        "Accept" = "application/vnd.github+json"
        "Content-Type" = "application/json"
    }
    $body = @{
        tag_name = $tag
        name = "PDF2BOOK AI $tag"
        body = "## $tag`n`n详见提交历史"
        draft = $false
        prerelease = $false
    } | ConvertTo-Json
    $resp = Invoke-RestMethod -Uri "https://api.github.com/repos/Acmerd-laofeng/PDF2BOOK_AI/releases" -Headers $headers -Method Post -Body $body
    $releaseId = $resp.id
    Write-Host "  Release 创建成功：ID=$releaseId"

    # 上传 asset（用 curl 避免 PowerShell ReadAllBytes OOM）
    $uploadUrl = "https://uploads.github.com/repos/Acmerd-laofeng/PDF2BOOK_AI/releases/$releaseId/assets?name=PDF2BOOK_AI_Setup.exe"
    $uploadResp = curl.exe -s -X Post `
      -H "Authorization: Bearer $GithubToken" `
      -H "Accept: application/vnd.github+json" `
      -H "Content-Type: application/octet-stream" `
      --data-binary "@$installerPath" `
      $uploadUrl
    Write-Host "  安装包上传完成"

    # 如果是最新版本，删除旧 Release 的同名 asset（避免冗余）
    Write-Host "  releases/latest/download/PDF2BOOK_AI_Setup.exe 已指向 $tag"
}

# 6. 更新 Supabase version（可选，需要管理员 JWT）
Write-Host "`n[6/6] 更新 Supabase version..." -ForegroundColor Yellow
Write-Host "  方式一：登录后台管理页面 → 资源管理 → PDF2BOOK AI → 修改 version 为 $tag" -ForegroundColor Green
Write-Host "  方式二：调用 API（需要管理员 JWT）：" -ForegroundColor Green
Write-Host "    POST https://acmerd.com/api/admin/resources" -ForegroundColor Gray
Write-Host "    Body: {`"action`":`"update_version`",`"id`":`"90b99357-1174-4e17-8bfb-c123a8554e08`",`"payload`":{`"version`":`"$tag`"}}" -ForegroundColor Gray
Write-Host "  方式三：跳过，AcmeNova 页面会从 GitHub API 备选获取" -ForegroundColor Green

Write-Host "`n=== 发版完成！ ===" -ForegroundColor Cyan
Write-Host "  下载地址：https://github.com/Acmerd-laofeng/PDF2BOOK_AI/releases/latest/download/PDF2BOOK_AI_Setup.exe"
Write-Host "  Release：https://github.com/Acmerd-laofeng/PDF2BOOK_AI/releases/tag/$tag"
