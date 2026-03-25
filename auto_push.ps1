$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $PSScriptRoot
$watcher.Filter = "*.*"
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$gitPath = (Get-Command git).Source
$ghPath = "C:\Program Files\GitHub CLI\gh.exe"

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    if ($name -notmatch ".git" -and $name -notmatch "auto_push.ps1") {
        Write-Host "[$(Get-Date)] 파일 변경 감지: $name" -ForegroundColor Cyan
        & $gitPath add .
        & $gitPath commit -m "Auto-sync update: $name"
        & $gitPath push origin master
        Write-Host "[$(Get-Date)] GitHub 푸시 완료!" -ForegroundColor Green
    }
}

Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
Register-ObjectEvent $watcher "Deleted" -Action $action | Out-Null

Write-Host "GitHub 자동 동기화 모니터링 시작 (종료하려면 Ctrl+C)" -ForegroundColor Yellow
while ($true) { Start-Sleep -Seconds 1 }
