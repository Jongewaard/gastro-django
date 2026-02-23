# Pizzería SaaS - Sistema Contable y Gestión de Personal

## 🎯 Objetivo
Sistema SaaS multi-tenant para gestión contable, inventarios y sueldos específicamente diseñado para pizzerías pequeñas y medianas.

## 📋 Características Principales

### 1. Multi-Tenancy (SaaS Core)
- Un sistema, múltiples pizzerías
- Datos completamente separados por tenant
- Facturación por pizzería
- Onboarding automatizado

### 2. Gestión de Ventas
- **Registro de ventas diarias**
  - Entrada manual rápida (caja registradora básica)
  - Categorías: pizzas, bebidas, postres, extras
  - Formas de pago: efectivo, tarjeta, transferencia
  - Descuentos y promociones
- **Reportes de ventas**
  - Diario, semanal, mensual
  - Por categoría de producto
  - Comparación con períodos anteriores

### 3. Control de Inventario
- **Ingredientes básicos**
  - Harina, queso, tomate, etc.
  - Control de stock mínimo
  - Alertas de reposición
- **Gestión de proveedores**
  - Contactos y datos de proveedores
  - Histórico de compras
- **Cálculo de costos**
  - Costo por pizza basado en ingredientes
  - Margen de ganancia por producto

### 4. Gestión de Personal
- **Empleados**
  - Datos personales básicos
  - Rol (cocinero, delivery, cajero, etc.)
  - Horarios de trabajo
- **Cálculo de sueldos**
  - Sueldos fijos + comisiones/propinas
  - Descuentos (ausencias, adelantos)
  - Liquidación mensual automática
- **Control de asistencia**
  - Check-in/check-out básico
  - Cálculo de horas trabajadas

### 5. Contabilidad Básica
- **Libro de ingresos y egresos**
  - Ventas (automáticas)
  - Gastos (compras, sueldos, servicios)
  - Categorización contable
- **Reportes fiscales**
  - IVA básico (si aplica)
  - Resumen mensual para contador
- **Dashboard financiero**
  - Cash flow
  - Rentabilidad por período

### 6. Features SaaS
- **Dashboard administrativo**
  - Métricas clave en tiempo real
  - Alertas y notificaciones
- **Gestión de usuarios**
  - Roles: Admin, Empleado, Contador
  - Permisos granulares
- **Backup automático**
  - Datos críticos respaldados
- **API REST** (futuro)
  - Integración con POS externos

## 🏗️ Arquitectura Técnica

### Stack Principal
- **Backend**: Django 5.0 + Django REST Framework
- **Base de datos**: PostgreSQL (multi-tenant con schemas)
- **Frontend**: Django Templates + HTMX + Alpine.js (progresivo)
- **CSS**: Tailwind CSS
- **Deploy**: Docker + nginx + gunicorn

### Estructura Multi-Tenant
```python
# Opción 1: Shared Database, Separate Schemas
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        # ... 
    }
}

# Opción 2: Tenant field en todos los modelos (más simple)
class Tenant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    # ...

class Sale(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    # ... resto del modelo
```

### Apps Django
1. **accounts** - Usuario, autenticación, tenants
2. **sales** - Ventas, productos, formas de pago
3. **inventory** - Ingredientes, stock, proveedores
4. **employees** - Personal, sueldos, asistencia
5. **accounting** - Contabilidad, reportes fiscales
6. **dashboard** - Métricas, alertas, notificaciones
7. **api** - REST API (futuro)

## 📱 UX/UI Simplificado

### Principios de diseño
- **Mobile-first**: Funciona en celular (dueños no siempre tienen PC)
- **Workflows rápidos**: 3 clicks máximo para tareas frecuentes
- **Visual claro**: Colores y iconos intuitivos
- **Mínimo entrenamiento**: Diseño obvio

### Pantallas clave
1. **Dashboard**: Ventas hoy, alertas, accesos rápidos
2. **Registrar venta**: Formulario ultra-simple
3. **Stock**: Semáforo verde/amarillo/rojo por ingrediente
4. **Empleados**: Lista con sueldos del mes
5. **Reportes**: Gráficos básicos, exportar PDF

## 🚀 Plan de Desarrollo (Fases)

### Fase 1: MVP Core (2-3 semanas)
- [ ] Setup proyecto Django + multi-tenant básico
- [ ] Autenticación y gestión de usuarios
- [ ] CRUD básico: Productos, Empleados
- [ ] Registro de ventas simple
- [ ] Dashboard básico con métricas

### Fase 2: Gestión Operativa (2 semanas)
- [ ] Control de inventario completo
- [ ] Cálculo de sueldos básico
- [ ] Reportes de ventas
- [ ] Sistema de alertas

### Fase 3: Contabilidad (2 semanas)
- [ ] Libro de ingresos/egresos
- [ ] Reportes fiscales básicos
- [ ] Integración con datos de ventas
- [ ] Export a Excel/PDF

### Fase 4: Polish & Deploy (1-2 semanas)
- [ ] UX/UI refinado
- [ ] Deploy en producción
- [ ] Testing con pizzería real
- [ ] Documentación de usuario

### Fase 5: SaaS Features (futuro)
- [ ] Onboarding automatizado
- [ ] Facturación por tenant
- [ ] API REST
- [ ] Integraciones externas

## 💰 Modelo de Negocio

### Pricing inicial
- **Plan Básico**: $15-25 USD/mes por pizzería
- **Plan Completo**: $35-50 USD/mes (con reportes avanzados)
- **Setup fee**: $100 USD (onboarding + capacitación)

### Value proposition
- Reduce tiempo en contabilidad manual
- Mejor control de costos e inventario
- Liquidación de sueldos automática
- Reportes listos para contador

## 🔧 Setup Inicial

### Dependencias principales
```txt
Django>=5.0
django-tenants>=3.6.0  # o django-tenant-schemas
djangorestframework>=3.14.0
psycopg2-binary>=2.9.0
django-extensions>=3.2.0
django-debug-toolbar>=4.0.0
celery>=5.3.0  # para tareas async
redis>=5.0.0   # broker para celery
```

### Variables de entorno
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/pizzeria_saas
REDIS_URL=redis://localhost:6379
EMAIL_HOST_USER=noreply@pizzeria-saas.com
```

## 🎯 Next Steps

1. **Setup proyecto** - estructura base Django + git
2. **Definir modelos** - empezar con User, Tenant, Sale
3. **Auth multi-tenant** - login con subdominio o path
4. **Primera funcionalidad** - registro de ventas
5. **Deploy temprano** - feedback real desde el inicio

---

**🍕 Target**: Sistema listo en 6-8 semanas para primera pizzería piloto.