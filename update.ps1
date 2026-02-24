# ============================================================
# Gastro SaaS - Update Script
# Verifica cambios en GitHub, descarga, migra y reinicia.
# ============================================================

$ErrorActionPreference = "Stop"
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PROJECT_DIR

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Gastro SaaS - Actualizacion" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---- 1. Verify git is available ----
try {
    $null = git --version
} catch {
    Write-Host "[ERROR] Git no esta instalado." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# ---- 2. Check we're in a git repo ----
if (-not (Test-Path ".git")) {
    Write-Host "[ERROR] Este directorio no es un repositorio git." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# ---- 3. Fetch remote changes ----
Write-Host "[1/5] Verificando cambios en el servidor..." -ForegroundColor Yellow
git fetch origin 2>&1 | Out-Null

$LOCAL = git rev-parse HEAD
$REMOTE = git rev-parse "origin/main"

if ($LOCAL -eq $REMOTE) {
    Write-Host ""
    Write-Host "[OK] El sistema ya esta actualizado. No hay cambios nuevos." -ForegroundColor Green
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 0
}

Write-Host "  Se encontraron cambios nuevos." -ForegroundColor White

# ---- 4. Show what changed ----
Write-Host ""
Write-Host "[2/5] Cambios pendientes:" -ForegroundColor Yellow
git log --oneline "$LOCAL..$REMOTE"
Write-Host ""

# Check if there are migration file changes
$DIFF_FILES = git diff --name-only "$LOCAL..$REMOTE"
$HAS_MIGRATIONS = $DIFF_FILES | Where-Object { $_ -match "migrations/" }
$HAS_REQUIREMENTS = $DIFF_FILES | Where-Object { $_ -match "requirements" }

# ---- 5. Pull changes ----
Write-Host "[3/5] Descargando cambios..." -ForegroundColor Yellow
try {
    git pull origin main 2>&1
    Write-Host "  Descarga completada." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Fallo el git pull. Verifica conflictos manualmente." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# ---- 6. Activate virtual environment ----
$VENV_ACTIVATE = Join-Path $PROJECT_DIR "venv\Scripts\Activate.ps1"
if (Test-Path $VENV_ACTIVATE) {
    & $VENV_ACTIVATE
} else {
    Write-Host "[WARN] No se encontro venv. Usando Python global." -ForegroundColor Yellow
}

# ---- 7. Update dependencies if requirements changed ----
if ($HAS_REQUIREMENTS) {
    Write-Host ""
    Write-Host "[3.5/5] Actualizando dependencias..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet 2>&1
    Write-Host "  Dependencias actualizadas." -ForegroundColor Green
}

# ---- 8. Run migrations if needed ----
Write-Host ""
if ($HAS_MIGRATIONS) {
    Write-Host "[4/5] Se detectaron cambios en la base de datos. Migrando..." -ForegroundColor Yellow
} else {
    Write-Host "[4/5] Verificando migraciones pendientes..." -ForegroundColor Yellow
}

try {
    $MIGRATE_OUTPUT = python manage.py migrate 2>&1
    $MIGRATE_OUTPUT | ForEach-Object { Write-Host "  $_" }
    Write-Host "  Migraciones completadas." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Fallo al migrar la base de datos." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# ---- 9. Restart server ----
Write-Host ""
Write-Host "[5/5] Reiniciando servidor..." -ForegroundColor Yellow

# Method 1: Stop via PID file
$PID_FILE = Join-Path $PROJECT_DIR ".server.pid"
if (Test-Path $PID_FILE) {
    $PID = Get-Content $PID_FILE -ErrorAction SilentlyContinue
    if ($PID) {
        try {
            $PROCESS = Get-Process -Id $PID -ErrorAction SilentlyContinue
            if ($PROCESS) {
                Stop-Process -Id $PID -Force -ErrorAction SilentlyContinue
                Write-Host "  Servidor anterior detenido (PID $PID)." -ForegroundColor White
                Start-Sleep -Seconds 2
            }
        } catch {}
    }
}

# Method 2: Kill any waitress process on port 8000
$PORT_PROCESSES = netstat -ano 2>$null | Select-String ":8000\s" | ForEach-Object {
    ($_ -split '\s+')[-1]
} | Sort-Object -Unique
foreach ($P in $PORT_PROCESSES) {
    if ($P -and $P -ne "0") {
        try {
            Stop-Process -Id $P -Force -ErrorAction SilentlyContinue
        } catch {}
    }
}

# Start server via run_server.pyw
$RUN_SCRIPT = Join-Path $PROJECT_DIR "run_server.pyw"
if (Test-Path $RUN_SCRIPT) {
    Start-Process pythonw $RUN_SCRIPT -WindowStyle Hidden
    Write-Host "  Servidor iniciado." -ForegroundColor Green
    Start-Sleep -Seconds 3

    # Quick health check
    try {
        $RESP = Invoke-WebRequest -Uri "http://localhost:8000/login/" -UseBasicParsing -TimeoutSec 5
        if ($RESP.StatusCode -eq 200) {
            Write-Host "  Servidor respondiendo correctamente." -ForegroundColor Green
        }
    } catch {
        Write-Host "  [WARN] El servidor esta iniciando, puede tardar unos segundos." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [WARN] No se encontro run_server.pyw. Reinicia el servidor manualmente." -ForegroundColor Yellow
}

# ---- Done ----
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Actualizacion completada!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Read-Host "Presiona Enter para salir"
