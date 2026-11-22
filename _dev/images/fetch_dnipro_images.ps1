# LBar Ivano-Frankivsk — завантаження потрібних фото з сайту Дніпра на ваш комп'ютер (Windows PowerShell 5+).
# Запуск: ПКМ по файлу -> "Выполнить с помощью PowerShell"
#   або:  powershell -ExecutionPolicy Bypass -File .\fetch_dnipro_images.ps1
# Файли складаються в папку .\lbar-frankovsk-images зі збереженням структури (images\..., assets\images\resources\...),
# її вміст потім заливається по FTP у корінь сайту. Повторний запуск докачує тільки відсутні файли.

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$list = Join-Path $here 'dnipro-images.tsv'
$outRoot = Join-Path $here 'lbar-frankovsk-images'
if (-not (Test-Path $list)) { Write-Host "Немає файлу dnipro-images.tsv поруч зі скриптом"; exit 1 }

$rows = Get-Content -Path $list -Encoding UTF8 | Select-Object -Skip 1 | Where-Object { $_.Trim() -ne '' }
$ok = 0; $skip = 0; $fail = 0; $failed = @()
$wc = New-Object System.Net.WebClient
$wc.Headers.Add('User-Agent', 'LBar-IF-image-sync')
$i = 0
foreach ($line in $rows) {
    $i++
    $p = $line -split "`t"
    $dest = $p[0].TrimStart('/'); $src = $p[1]; $fb = if ($p.Count -gt 2) { $p[2] } else { '' }
    if ($dest -eq '' -or $dest.Contains('..')) { continue }
    $target = Join-Path $outRoot ($dest -replace '/', '\')
    if ((Test-Path $target) -and ((Get-Item $target).Length -gt 0)) { $skip++; continue }
    $dir = Split-Path -Parent $target
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $done = $false
    foreach ($u in @($src, $fb)) {
        if ([string]::IsNullOrWhiteSpace($u)) { continue }
        try { $wc.DownloadFile($u, $target); $done = $true; break } catch { if (Test-Path $target) { Remove-Item $target -Force } }
    }
    if ($done) { $ok++; Write-Host ("[{0}/{1}] OK   {2}" -f $i, $rows.Count, $dest) }
    else { $fail++; $failed += $dest; Write-Host ("[{0}/{1}] FAIL {2}" -f $i, $rows.Count, $dest) -ForegroundColor Red }
}
Write-Host ""
Write-Host "Завантажено: $ok, вже були: $skip, помилок: $fail"
if ($failed.Count -gt 0) { $failed | Out-File -FilePath (Join-Path $here 'failed.txt') -Encoding UTF8; Write-Host "Список помилок: failed.txt" }
Write-Host "Папка з файлами: $outRoot"
Read-Host "Натисніть Enter, щоб закрити"
