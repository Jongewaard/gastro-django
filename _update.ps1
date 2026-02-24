# ============================================================
# Gastro SaaS - Actualizador
# NO ejecutar directamente - usar ACTUALIZAR.bat
# O desde terminal: powershell -ExecutionPolicy Bypass -File _update.ps1
# ============================================================

$Port = 8000

# --- Helpers ---
function Write-Step($num, $total, $msg) {
    Write-Host ""
    Write-Host "[$num/$total] $msg" -ForegroundColor Yellow
}
function Write-Ok($msg) {
    Write-Host "  [OK] $msg" -ForegroundColor Green
}
function Write-Fail($msg) {
    Write-Host "  [ERROR] $msg" -ForegroundColor Red
}
function Write-Warn($msg) {
    Write-Host "  [AVISO] $msg" -ForegroundColor Yellow
}
function Bail($msg) {
    Write-Host ""
    Write-Fail $msg
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}
function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# --- Ubicarnos en la carpeta del script ---
try {
    $PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $PROJECT_DIR
} catch {
    Bail "No se pudo determinar la carpeta del script."
}

# Rutas del venv (usar siempre estas, nunca el python global)
$venvPython = Join-Path $PROJECT_DIR "venv\Scripts\python.exe"
$venvPip = Join-Path $PROJECT_DIR "venv\Scripts\pip.exe"
$venvPythonW = Join-Path $PROJECT_DIR "venv\Scripts\pythonw.exe"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Gastro SaaS - Actualizacion" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Carpeta: $PROJECT_DIR" -ForegroundColor Gray

# ============================================================
# 0. Pre-checks
# ============================================================

# Check venv exists
if (-not (Test-Path $venvPython)) {
    Bail "No se encontro el entorno virtual. Ejecuta INSTALAR.bat primero."
}

# Check Git
$gitOk = $false
try {
    $gitVer = & git --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $gitVer -match "git version") {
        $gitOk = $true
    }
} catch {}

if (-not $gitOk) {
    Write-Host ""
    Write-Warn "Git no esta instalado. Es necesario para actualizar."
    Write-Host ""
    $resp = Read-Host "  Queres que intente instalarlo? (S/N)"
    if ($resp -match "^[sS]") {
        try {
            Write-Host "  Instalando Git..." -ForegroundColor Yellow
            & winget install Git.Git --accept-package-agreements --accept-source-agreements --silent 2>&1 | Out-Null
            Refresh-Path
            $gitVer = & git --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "Git instalado: $gitVer"
                Write-Host ""
                Write-Warn "Necesitas cerrar y volver a abrir esta ventana para que Git funcione."
                Write-Host "  Luego ejecuta ACTUALIZAR.bat de nuevo." -ForegroundColor Yellow
                Read-Host "Presiona Enter para salir"
                exit 0
            }
        } catch {}
        Bail "No se pudo instalar Git. Descargalo desde https://git-scm.com/downloads"
    } else {
        Bail "Sin Git no se puede actualizar. Instalalo desde https://git-scm.com/downloads"
    }
}

# Check we're in a git repo
if (-not (Test-Path ".git")) {
    Bail "Este directorio no es un repositorio git. Verifica la carpeta."
}

# Check remote is configured
$remoteUrl = & git remote get-url origin 2>&1
if ($LASTEXITCODE -ne 0) {
    Bail "No hay un repositorio remoto configurado (origin). Verifica con el administrador."
}

# ============================================================
# 1. Check for remote changes
# ============================================================
Write-Step 1 5 "Verificando cambios en el servidor..."

# Test internet/repo connectivity
$fetchOut = & git fetch origin 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Salida: $fetchOut" -ForegroundColor Gray
    Bail "No se pudo conectar al servidor. Verifica tu conexion a internet."
}

$LOCAL = & git rev-parse HEAD 2>&1
$REMOTE = & git rev-parse "origin/main" 2>&1

if ($LASTEXITCODE -ne 0) {
    Bail "No se pudo determinar el estado del repositorio."
}

if ($LOCAL -eq $REMOTE) {
    Write-Host ""
    Write-Ok "El sistema ya esta actualizado. No hay cambios nuevos."
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 0
}

# ============================================================
# 2. Show what will change
# ============================================================
Write-Step 2 5 "Cambios pendientes:"

& git log --oneline "$LOCAL..$REMOTE"
Write-Host ""

# Detect what kind of changes are coming
$DIFF_FILES = & git diff --name-only "$LOCAL..$REMOTE" 2>&1
$HAS_MIGRATIONS = $DIFF_FILES | Where-Object { $_ -match "migrations/" }
$HAS_REQUIREMENTS = $DIFF_FILES | Where-Object { $_ -match "requirements" }

if ($HAS_MIGRATIONS) {
    Write-Host "  * Incluye cambios en la base de datos" -ForegroundColor Magenta
}
if ($HAS_REQUIREMENTS) {
    Write-Host "  * Incluye cambios en dependencias" -ForegroundColor Magenta
}

# ============================================================
# 3. Pull changes
# ============================================================
Write-Step 3 5 "Descargando cambios..."

# Check for local uncommitted changes that could conflict
$localChanges = & git status --porcelain 2>&1
if ($localChanges) {
    Write-Warn "Hay archivos modificados localmente. Guardando cambios temporales..."
    & git stash --include-untracked 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Bail "No se pudieron guardar los cambios locales. Contacta al administrador."
    }
    Write-Ok "Cambios locales guardados (se restauraran despues)"
}

$pullOut = & git pull origin main 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  $pullOut" -ForegroundColor Red
    # Try to restore stash if we stashed
    if ($localChanges) {
        & git stash pop 2>&1 | Out-Null
    }
    Bail "Fallo la descarga. Contacta al administrador."
}
Write-Ok "Descarga completada"

# Restore stashed changes if any
if ($localChanges) {
    & git stash pop 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Algunos cambios locales pueden tener conflictos. Revisa manualmente."
    } else {
        Write-Ok "Cambios locales restaurados"
    }
}

# ============================================================
# 4. Update dependencies + migrate
# ============================================================

# 4a. Dependencies
if ($HAS_REQUIREMENTS) {
    Write-Step 4 5 "Actualizando dependencias..."
    & $venvPython -m pip install --quiet -r requirements.txt 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Hubo un problema instalando dependencias. El sistema puede funcionar igual."
    } else {
        Write-Ok "Dependencias actualizadas"
    }
} else {
    Write-Step 4 5 "Verificando base de datos..."
}

# 4b. Migrations (always run - safe to run even without changes)
$migrateOut = & $venvPython manage.py migrate 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Error en las migraciones:"
    $migrateOut | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Write-Host ""
    Write-Warn "La actualizacion del codigo se completo pero la base de datos puede tener problemas."
    Write-Host "  Contacta al administrador." -ForegroundColor Yellow
} else {
    Write-Ok "Base de datos actualizada"
}

# ============================================================
# 5. Restart server
# ============================================================
Write-Step 5 5 "Reiniciando servidor..."

# Stop via PID file
$pidFile = Join-Path $PROJECT_DIR ".server.pid"
$stopped = $false

if (Test-Path $pidFile) {
    $oldPid = (Get-Content $pidFile -ErrorAction SilentlyContinue).Trim()
    if ($oldPid -match '^\d+$') {
        try {
            $proc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
                Write-Host "  Servidor detenido (PID $oldPid)" -ForegroundColor Gray
                Start-Sleep -Seconds 2
                $stopped = $true
            }
        } catch {}
    }
}

# Fallback: kill pythonw running run_server
if (-not $stopped) {
    Get-Process -Name "pythonw" -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $cmdline = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine
            if ($cmdline -and $cmdline -match "run_server") {
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
            }
        } catch {}
    }
}

# Start server
$runScript = Join-Path $PROJECT_DIR "run_server.pyw"
if (Test-Path $runScript) {
    Start-Process -FilePath $venvPythonW -ArgumentList "`"$runScript`"" -WorkingDirectory $PROJECT_DIR -WindowStyle Hidden
    Start-Sleep -Seconds 4

    # Health check con reintentos
    $serverOk = $false
    for ($i = 1; $i -le 3; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:$Port/login/" -UseBasicParsing -TimeoutSec 5
            if ($resp.StatusCode -eq 200) {
                $serverOk = $true
                break
            }
        } catch {}
        Start-Sleep -Seconds 2
    }

    if ($serverOk) {
        Write-Ok "Servidor funcionando correctamente"
    } else {
        Write-Warn "El servidor esta iniciando... puede tardar unos segundos."
        Write-Host "  Si no funciona, revisa 'server.log' o ejecuta INSTALAR.bat" -ForegroundColor Yellow
    }
} else {
    Write-Warn "No se encontro run_server.pyw. Reinicia el servidor manualmente."
}

# ============================================================
# Done
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Actualizacion completada!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Read-Host "Presiona Enter para salir"
