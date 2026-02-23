# 🛠️ Comandos Útiles - Pizzería SaaS

## Setup inicial
```bash
# Activar virtual environment
venv\Scripts\activate

# Instalar todas las dependencias
pip install -r requirements.txt

# Crear archivo .env (copiar desde .env.example)
copy .env.example .env

# Primera migración
python manage.py makemigrations
python manage.py migrate

# Crear superuser
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

## Desarrollo diario
```bash
# Activar entorno
venv\Scripts\activate

# Instalar nueva dependencia
pip install package_name
pip freeze > requirements.txt

# Crear nueva app
python manage.py startapp app_name

# Migrations
python manage.py makemigrations
python manage.py migrate

# Shell interactivo
python manage.py shell

# Tests
python manage.py test

# Collectstatic (para producción)
python manage.py collectstatic
```

## Git workflow
```bash
# Ver estado
git status

# Agregar archivos
git add .
git add archivo_especifico.py

# Commit
git commit -m "Descripción del cambio"

# Ver histórico
git log --oneline

# Crear nueva rama
git checkout -b feature/nueva-funcionalidad

# Cambiar entre ramas  
git checkout main
git checkout feature/otra-rama

# Merge rama
git checkout main
git merge feature/nueva-funcionalidad
```

## Multi-tenant (cuando se implemente)
```bash
# Migrar schemas compartidos
python manage.py migrate_schemas --shared

# Migrar todos los tenants
python manage.py migrate_schemas

# Crear nuevo tenant
python manage.py create_tenant

# Migrar tenant específico
python manage.py migrate_schemas --tenant=pizzeria1
```

## Debugging
```bash
# Shell con imports automáticos
python manage.py shell_plus

# Ejecutar con debugging
python manage.py runserver --settings=pizzeria_saas.settings_debug

# Ver queries SQL
python manage.py shell
# >>> from django.db import connection
# >>> connection.queries
```

## Producción (futuro)
```bash
# Variables de entorno prod
export DEBUG=False
export DATABASE_URL=postgresql://...

# Gunicorn
gunicorn pizzeria_saas.wsgi:application

# Celery (tareas async)
celery -A pizzeria_saas worker -l info
celery -A pizzeria_saas beat -l info
```

## Útiles para este proyecto específico
```bash
# Reset completo de DB (desarrollo)
python manage.py reset_db --noinput
python manage.py migrate

# Cargar datos de ejemplo
python manage.py loaddata fixtures/sample_data.json

# Backup DB local
python manage.py dumpdata > backup.json

# Verificar configuración
python manage.py check
python manage.py check --deploy
```