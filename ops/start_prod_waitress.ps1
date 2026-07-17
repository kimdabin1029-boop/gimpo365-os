Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = "E:\gimpo365\gimpo365-os"
$WaitressExe = Join-Path $ProjectRoot ".venv\Scripts\waitress-serve.exe"
$LogDirectory = Join-Path $ProjectRoot "var\logs"
$SupervisorLog = Join-Path $LogDirectory "waitress-prod-supervisor.log"

New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null

if (-not (Test-Path $WaitressExe)) {
    throw "Waitress 실행 파일을 찾을 수 없습니다: $WaitressExe"
}

$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$StdoutLog = Join-Path $LogDirectory "waitress-prod-$RunId.stdout.log"
$StderrLog = Join-Path $LogDirectory "waitress-prod-$RunId.stderr.log"

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Waitress starting" |
    Out-File -FilePath $SupervisorLog -Append -Encoding utf8

"Executable: $WaitressExe" |
    Out-File -FilePath $SupervisorLog -Append -Encoding utf8

"STDOUT: $StdoutLog" |
    Out-File -FilePath $SupervisorLog -Append -Encoding utf8

"STDERR: $StderrLog" |
    Out-File -FilePath $SupervisorLog -Append -Encoding utf8

$WaitressArguments = @(
    "--listen=0.0.0.0:8000"
    "--threads=4"
    "config.wsgi:application"
)

$Process = Start-Process `
    -FilePath $WaitressExe `
    -ArgumentList $WaitressArguments `
    -WorkingDirectory $ProjectRoot `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -Wait `
    -PassThru

$ExitCode = $Process.ExitCode

"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Waitress stopped. Exit code: $ExitCode" |
    Out-File -FilePath $SupervisorLog -Append -Encoding utf8

exit $ExitCode