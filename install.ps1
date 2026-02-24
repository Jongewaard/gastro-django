# ============================================================
# Gastro SaaS - Instalador / Actualizador
# Ejecutar como: powershell -ExecutionPolicy Bypass -File install.ps1
# Idempotente: se puede ejecutar multiples veces sin romper nada
# ============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$ServiceName = "GastroSaaS_Server"
$Port = 8000

function Write-Step($msg) {
    Write-Host ""
    Write-Host ">> $msg" -ForegroundColor Cyan
}

function Write-Ok($msg) {
    Write-Host "   [OK] $msg" -ForegroundColor Green
}

function Write-Skip($msg) {
    Write-Host "   [SKIP] $msg" -ForegroundColor Yellow
}

function Write-Fail($msg) {
    Write-Host "   [ERROR] $msg" -ForegroundColor Red
}

# ============================================================
# 1. Verificar Git
# ============================================================
Write-Step "Verificando Git..."

$gitOk = $false
try {
    $gitVer = git --version 2>&1
    if ($gitVer -match "git version") {
        Write-Ok "Git encontrado: $gitVer"
        $gitOk = $true
    }
} catch {}

if (-not $gitOk) {
    Write-Step "Instalando Git via winget..."
    try {
        winget install Git.Git --accept-package-agreements --accept-source-agreements --silent
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $gitVer = git --version 2>&1
        Write-Ok "Git instalado: $gitVer"
    } catch {
        Write-Fail "No se pudo instalar Git automaticamente."
        Write-Host "   Descargalo desde https://git-scm.com/downloads" -ForegroundColor Yellow
        Write-Host "   (Necesario para recibir actualizaciones)" -ForegroundColor Yellow
        # No salimos, el sistema funciona sin git, solo no puede actualizarse
    }
}

# ============================================================
# 2. Verificar Python
# ============================================================
Write-Step "Verificando Python..."

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -ge 10) {
                $pythonCmd = $cmd
                Write-Ok "Python encontrado: $ver"
                break
            }
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Step "Instalando Python via winget..."
    try {
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $pythonCmd = "python"
        $ver = & python --version 2>&1
        Write-Ok "Python instalado: $ver"
    } catch {
        Write-Fail "No se pudo instalar Python automaticamente."
        Write-Host "   Descargalo manualmente desde https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "   IMPORTANTE: Marca 'Add Python to PATH' durante la instalacion." -ForegroundColor Yellow
        Read-Host "Presiona Enter para salir"
        exit 1
    }
}

# ============================================================
# 3. Crear entorno virtual (si no existe)
# ============================================================
Write-Step "Verificando entorno virtual..."

$venvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"
$venvPythonW = Join-Path $ScriptDir "venv\Scripts\pythonw.exe"

if (Test-Path $venvPython) {
    Write-Skip "El entorno virtual ya existe"
} else {
    Write-Host "   Creando entorno virtual..."
    & $pythonCmd -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Error al crear el entorno virtual"
        exit 1
    }
    Write-Ok "Entorno virtual creado"
}

# ============================================================
# 4. Instalar dependencias
# ============================================================
Write-Step "Instalando/actualizando dependencias..."

& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Fail "Error al instalar dependencias"
    exit 1
}
Write-Ok "Dependencias instaladas"

# ============================================================
# 5. Migraciones de base de datos
# ============================================================
Write-Step "Ejecutando migraciones..."

& $venvPython manage.py migrate --run-syncdb 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Error en las migraciones"
    exit 1
}
Write-Ok "Base de datos actualizada"

# ============================================================
# 6. Crear superusuario (solo si no existe ninguno)
# ============================================================
Write-Step "Verificando superusuario..."

$hasSuperuser = & $venvPython -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_saas.settings')
django.setup()
from accounts.models import User
print('yes' if User.objects.filter(is_superuser=True).exists() else 'no')
" 2>&1

if ($hasSuperuser -eq "yes") {
    Write-Skip "Ya existe un superusuario"
} else {
    Write-Host "   Creando superusuario..."
    Write-Host ""
    Write-Host "   Ingresa los datos del administrador:" -ForegroundColor Yellow

    $username = Read-Host "   Usuario"
    $email = Read-Host "   Email (opcional, Enter para omitir)"
    if (-not $email) { $email = "" }

    & $venvPython -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_saas.settings')
django.setup()
from accounts.models import User
user = User.objects.create_superuser('$username', '$email', input('   Contrasena: '))
user.role = 'owner'
user.save()
print('OK')
"
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Error al crear superusuario"
    } else {
        Write-Ok "Superusuario creado"
    }
}

# ============================================================
# 7. Detener servidor previo (si esta corriendo)
# ============================================================
Write-Step "Verificando servidor previo..."

$running = Get-Process -Name "pythonw" -ErrorAction SilentlyContinue |
    Where-Object {
        try {
            $cmdline = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
            $cmdline -match "run_server\.pyw"
        } catch { $false }
    }

if ($running) {
    Write-Host "   Deteniendo servidor anterior..."
    $running | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Ok "Servidor anterior detenido"
} else {
    Write-Skip "No hay servidor corriendo"
}

# ============================================================
# 8. Registrar tarea programada (inicio con Windows)
# ============================================================
Write-Step "Configurando inicio automatico..."

$taskExists = schtasks /Query /TN $ServiceName 2>&1
if ($taskExists -match $ServiceName) {
    Write-Skip "La tarea programada ya existe, actualizando..."
    schtasks /Delete /TN $ServiceName /F 2>&1 | Out-Null
}

$taskCmd = "`"$venvPythonW`" `"$(Join-Path $ScriptDir 'run_server.pyw')`""

schtasks /Create /TN $ServiceName /TR $taskCmd /SC ONSTART /RU "$env:USERNAME" /F /RL HIGHEST 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    # Si ONSTART falla (requiere admin), intentar con ONLOGON
    schtasks /Create /TN $ServiceName /TR $taskCmd /SC ONLOGON /F 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "No se pudo crear la tarea programada"
        Write-Host "   El servidor funcionara pero no se iniciara automaticamente con Windows" -ForegroundColor Yellow
    } else {
        Write-Ok "Tarea programada creada (se inicia al iniciar sesion)"
    }
} else {
    Write-Ok "Tarea programada creada (se inicia con Windows)"
}

# ============================================================
# 9. Crear carpeta de backups
# ============================================================
$backupDir = Join-Path $ScriptDir "backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Ok "Carpeta de backups creada"
}

# ============================================================
# 10. Crear accesos directos en el escritorio
# ============================================================
Write-Step "Creando accesos directos..."

$desktop = [Environment]::GetFolderPath("Desktop")
$WshShell = New-Object -ComObject WScript.Shell

# Shortcut: Abrir Gastro SaaS
$shortcut = $WshShell.CreateShortcut("$desktop\Gastro SaaS.lnk")
$shortcut.TargetPath = "http://localhost:$Port"
$shortcut.IconLocation = "shell32.dll,14"
$shortcut.Description = "Abrir Gastro SaaS en el navegador"
$shortcut.Save()
Write-Ok "Acceso directo 'Gastro SaaS' creado en el escritorio"

# ============================================================
# 11. Iniciar servidor
# ============================================================
Write-Step "Iniciando servidor..."

Start-Process -FilePath $venvPythonW -ArgumentList "`"$(Join-Path $ScriptDir 'run_server.pyw')`"" -WorkingDirectory $ScriptDir -WindowStyle Hidden

Start-Sleep -Seconds 3

# Verificar que esta corriendo
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$Port/login/" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Ok "Servidor iniciado correctamente en http://localhost:$Port"
    }
} catch {
    Write-Host "   Servidor iniciando... puede tardar unos segundos mas" -ForegroundColor Yellow
}

# ============================================================
# Resumen final
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Gastro SaaS - Instalacion completa" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  URL:  http://localhost:$Port" -ForegroundColor White
Write-Host "  Admin: http://localhost:$Port/admin/" -ForegroundColor White
Write-Host ""
Write-Host "  El servidor se inicia automaticamente con Windows." -ForegroundColor Gray
Write-Host "  Podes reiniciarlo desde la seccion 'Copias de Seguridad'" -ForegroundColor Gray
Write-Host "  o ejecutando este script de nuevo." -ForegroundColor Gray
Write-Host ""

# Abrir en el navegador
Start-Process "http://localhost:$Port"

Read-Host "Presiona Enter para cerrar"
