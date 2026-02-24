# ============================================================
# Gastro SaaS - Instalador
# Ejecutar: click derecho → "Ejecutar con PowerShell"
# O desde terminal: powershell -ExecutionPolicy Bypass -File install.ps1
# Idempotente: se puede ejecutar multiples veces sin romper nada
# ============================================================

$ServiceName = "GastroSaaS_Server"
$Port = 8000

# --- Helpers ---
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
function Write-Warn($msg) {
    Write-Host "   [AVISO] $msg" -ForegroundColor Yellow
}

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# --- Ubicarnos en la carpeta del script ---
try {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $ScriptDir
} catch {
    Write-Host "[ERROR] No se pudo determinar la carpeta del script." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Gastro SaaS - Instalador" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Carpeta: $ScriptDir" -ForegroundColor Gray

# ============================================================
# 1. Verificar Git
# ============================================================
Write-Step "Verificando Git..."

$gitOk = $false
try {
    $gitVer = & git --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $gitVer -match "git version") {
        Write-Ok "Git encontrado: $gitVer"
        $gitOk = $true
    }
} catch {}

if (-not $gitOk) {
    Write-Host "   Git no encontrado. Intentando instalar..." -ForegroundColor Yellow
    try {
        & winget install Git.Git --accept-package-agreements --accept-source-agreements --silent 2>&1 | Out-Null
        Refresh-Path
        $gitVer = & git --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Git instalado: $gitVer"
            $gitOk = $true
        }
    } catch {}

    if (-not $gitOk) {
        Write-Warn "No se pudo instalar Git automaticamente."
        Write-Host "   Descargalo desde https://git-scm.com/downloads" -ForegroundColor Yellow
        Write-Host "   Sin Git no podras recibir actualizaciones, pero el sistema funciona." -ForegroundColor Yellow
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
        if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3\.(\d+)") {
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
    Write-Host "   Python no encontrado. Intentando instalar..." -ForegroundColor Yellow
    try {
        & winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent 2>&1 | Out-Null
        Refresh-Path
        $ver = & python --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") {
            $pythonCmd = "python"
            Write-Ok "Python instalado: $ver"
        }
    } catch {}

    if (-not $pythonCmd) {
        Write-Fail "No se pudo instalar Python."
        Write-Host "   Descargalo desde https://www.python.org/downloads/" -ForegroundColor Yellow
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
$venvPip = Join-Path $ScriptDir "venv\Scripts\pip.exe"
$venvPythonW = Join-Path $ScriptDir "venv\Scripts\pythonw.exe"

if (Test-Path $venvPython) {
    Write-Skip "El entorno virtual ya existe"
} else {
    Write-Host "   Creando entorno virtual..."
    & $pythonCmd -m venv venv 2>&1
    if (-not (Test-Path $venvPython)) {
        Write-Fail "Error al crear el entorno virtual"
        Read-Host "Presiona Enter para salir"
        exit 1
    }
    Write-Ok "Entorno virtual creado"
}

# ============================================================
# 4. Instalar dependencias
# ============================================================
Write-Step "Instalando/actualizando dependencias..."

& $venvPython -m pip install --quiet --upgrade pip 2>&1 | Out-Null
& $venvPython -m pip install --quiet -r requirements.txt 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Error al instalar dependencias. Verifica tu conexion a internet."
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Ok "Dependencias instaladas"

# ============================================================
# 5. Migraciones de base de datos
# ============================================================
Write-Step "Ejecutando migraciones..."

$migrateOut = & $venvPython manage.py migrate --run-syncdb 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Error en las migraciones:"
    $migrateOut | ForEach-Object { Write-Host "   $_" -ForegroundColor Red }
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Ok "Base de datos actualizada"

# ============================================================
# 6. Crear superusuario (solo si no existe ninguno)
# ============================================================
Write-Step "Verificando superusuario..."

$hasSuperuser = & $venvPython -c "import django,os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','pizzeria_saas.settings');django.setup();from accounts.models import User;print('yes' if User.objects.filter(is_superuser=True).exists() else 'no')" 2>&1

if ($hasSuperuser.Trim() -eq "yes") {
    Write-Skip "Ya existe un superusuario"
} else {
    Write-Host "   Creando superusuario..." -ForegroundColor White
    Write-Host ""
    Write-Host "   Ingresa los datos del administrador:" -ForegroundColor Yellow

    $username = Read-Host "   Usuario"
    if (-not $username) { $username = "admin" }

    $email = Read-Host "   Email (opcional, Enter para omitir)"
    if (-not $email) { $email = "" }

    $password = Read-Host "   Contrasena"
    if (-not $password) {
        Write-Fail "La contrasena no puede estar vacia."
        Read-Host "Presiona Enter para salir"
        exit 1
    }

    # Use environment variables to avoid injection issues with special characters
    $env:GASTRO_SU_USER = $username
    $env:GASTRO_SU_EMAIL = $email
    $env:GASTRO_SU_PASS = $password

    & $venvPython -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_saas.settings')
django.setup()
from accounts.models import User
u = User.objects.create_superuser(
    os.environ['GASTRO_SU_USER'],
    os.environ.get('GASTRO_SU_EMAIL', ''),
    os.environ['GASTRO_SU_PASS']
)
u.role = 'owner'
u.save()
print('OK')
" 2>&1

    # Clean up env vars
    Remove-Item Env:GASTRO_SU_USER -ErrorAction SilentlyContinue
    Remove-Item Env:GASTRO_SU_EMAIL -ErrorAction SilentlyContinue
    Remove-Item Env:GASTRO_SU_PASS -ErrorAction SilentlyContinue

    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Error al crear superusuario"
    } else {
        Write-Ok "Superusuario '$username' creado"
    }
}

# ============================================================
# 7. Detener servidor previo (si esta corriendo)
# ============================================================
Write-Step "Verificando servidor previo..."

$stopped = $false

# Via PID file
$pidFile = Join-Path $ScriptDir ".server.pid"
if (Test-Path $pidFile) {
    $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($oldPid) {
        try {
            $proc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
                $stopped = $true
            }
        } catch {}
    }
}

# Via process name (fallback)
if (-not $stopped) {
    $running = Get-Process -Name "pythonw" -ErrorAction SilentlyContinue |
        Where-Object {
            try {
                $cmdline = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine
                $cmdline -and $cmdline -match "run_server"
            } catch { $false }
        }
    if ($running) {
        $running | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        $stopped = $true
    }
}

if ($stopped) {
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
    schtasks /Delete /TN $ServiceName /F 2>&1 | Out-Null
}

$taskCmd = "`"$venvPythonW`" `"$(Join-Path $ScriptDir 'run_server.pyw')`""

# Try ONSTART first (needs admin), fallback to ONLOGON
$created = $false
schtasks /Create /TN $ServiceName /TR $taskCmd /SC ONSTART /RU "$env:USERNAME" /F /RL HIGHEST 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Inicio automatico configurado (al encender la PC)"
    $created = $true
}

if (-not $created) {
    schtasks /Create /TN $ServiceName /TR $taskCmd /SC ONLOGON /F 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Inicio automatico configurado (al iniciar sesion)"
        $created = $true
    }
}

if (-not $created) {
    Write-Warn "No se pudo configurar el inicio automatico."
    Write-Host "   El servidor funciona, pero deberas iniciarlo manualmente." -ForegroundColor Yellow
}

# ============================================================
# 9. Crear carpetas necesarias
# ============================================================
foreach ($dir in @("backups", "media")) {
    $dirPath = Join-Path $ScriptDir $dir
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
    }
}

# ============================================================
# 10. Crear accesos directos en el escritorio
# ============================================================
Write-Step "Creando accesos directos..."

try {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $WshShell = New-Object -ComObject WScript.Shell

    $shortcut = $WshShell.CreateShortcut("$desktop\Gastro SaaS.lnk")
    $shortcut.TargetPath = "http://localhost:$Port"
    $shortcut.IconLocation = "shell32.dll,14"
    $shortcut.Description = "Abrir Gastro SaaS en el navegador"
    $shortcut.Save()
    Write-Ok "Acceso directo 'Gastro SaaS' creado en el escritorio"
} catch {
    Write-Warn "No se pudo crear el acceso directo."
}

# ============================================================
# 11. Iniciar servidor
# ============================================================
Write-Step "Iniciando servidor..."

$runScript = Join-Path $ScriptDir "run_server.pyw"
if (-not (Test-Path $runScript)) {
    Write-Fail "No se encontro run_server.pyw"
    Read-Host "Presiona Enter para salir"
    exit 1
}

Start-Process -FilePath $venvPythonW -ArgumentList "`"$runScript`"" -WorkingDirectory $ScriptDir -WindowStyle Hidden
Start-Sleep -Seconds 4

# Health check con reintentos
$serverOk = $false
for ($i = 1; $i -le 3; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port/login/" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $serverOk = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 2
}

if ($serverOk) {
    Write-Ok "Servidor iniciado en http://localhost:$Port"
} else {
    Write-Warn "El servidor esta iniciando... puede tardar unos segundos."
    Write-Host "   Si no abre, revisa el archivo 'server.log' para ver errores." -ForegroundColor Yellow
}

# ============================================================
# Resumen final
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Gastro SaaS - Instalacion completa!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  URL:   http://localhost:$Port" -ForegroundColor White
Write-Host "  Admin: http://localhost:$Port/admin/" -ForegroundColor White
Write-Host ""
Write-Host "  El servidor se inicia automaticamente con Windows." -ForegroundColor Gray
Write-Host "  Para actualizar, ejecuta update.ps1" -ForegroundColor Gray
Write-Host ""

Start-Process "http://localhost:$Port"
Read-Host "Presiona Enter para cerrar"
