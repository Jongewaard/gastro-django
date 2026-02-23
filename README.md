# 🍕 Pizzería SaaS

Sistema de gestión contable, inventarios y sueldos para pizzerías. Multi-tenant SaaS desarrollado en Django.

## 🚀 Quick Start

### 1. Setup del proyecto
```bash
# Crear virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
# Editar .env con tus configuraciones
```

### 2. Base de datos
```bash
# Instalar PostgreSQL y crear DB
createdb pizzeria_saas

# Migrations
python manage.py makemigrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
```

### 3. Ejecutar servidor
```bash
python manage.py runserver
```

## 🏗️ Arquitectura

- **Multi-tenant**: Un sistema, múltiples pizzerías
- **Django 5.0**: Framework principal
- **PostgreSQL**: Base de datos con schemas separados
- **Tailwind CSS**: Styling moderno
- **HTMX**: Interactividad sin JS complejo

## 📚 Documentación

Ver `PLAN_PROYECTO.md` para detalles completos del plan y arquitectura.

## 🤝 Contribuir

Este proyecto está en desarrollo activo. Cualquier feedback es bienvenido.

## 📄 Licencia

Proyecto privado - todos los derechos reservados.