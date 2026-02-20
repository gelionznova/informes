Param(
    [string]$PythonVersion = "3.11",
    [string]$VenvName = ".venv_clean311",
    [switch]$Sign,
    [string]$CertificateThumbprint,
    [string]$TimeStampUrl = "http://timestamp.digicert.com",
    [string]$SignToolPath = "signtool"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot

Push-Location $projectRoot
try {
    Write-Host "[1/5] Creando/actualizando entorno virtual: $VenvName"
    py -$PythonVersion -m venv $VenvName

    $pythonExe = Join-Path $projectRoot "$VenvName\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        throw "No se encontró Python del entorno virtual en: $pythonExe"
    }

    Write-Host "[2/5] Instalando dependencias"
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r "app\requirements.txt"
    & $pythonExe -m pip install pyinstaller

    Write-Host "[3/5] Generando ejecutable con PyInstaller"
    & $pythonExe -m PyInstaller --clean --noconfirm --log-level=INFO --onefile --noconsole --add-data "app\templates;templates" --add-data "app\static;static" --add-data "app\docx_templates;docx_templates" --add-data "app\data;data" "app\app.py"

    $exePath = Join-Path $projectRoot "dist\app.exe"
    if (-not (Test-Path $exePath)) {
        throw "No se generó el ejecutable esperado en: $exePath"
    }

    if ($Sign) {
        Write-Host "[4/5] Firmando ejecutable"
        $signArgs = @("sign", "/fd", "SHA256", "/tr", $TimeStampUrl, "/td", "SHA256")

        if ($CertificateThumbprint) {
            $signArgs += @("/sha1", $CertificateThumbprint)
        }
        else {
            $signArgs += "/a"
        }

        $signArgs += $exePath
        & $SignToolPath @signArgs

        Write-Host "[5/5] Verificando firma"
        & $SignToolPath verify /pa /v $exePath
    }
    else {
        Write-Host "[4/5] Firma omitida (usa -Sign para firmar)"
        Write-Host "[5/5] Proceso completado"
    }

    Write-Host "Listo: $exePath"
}
finally {
    Pop-Location
}
