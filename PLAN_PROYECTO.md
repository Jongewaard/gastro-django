# Gastro SaaS - Sistema Universal para Negocios Gastronómicos

## 🎯 Objetivo ACTUALIZADO
Sistema SaaS multi-tenant para gestión integral de **cualquier negocio gastronómico**: pizzerías, heladerías, restaurantes, cafeterías, etc. 

## 📋 Características Principales

### 1. Multi-Tenancy Configurable
- Un sistema, múltiples negocios gastronómicos
- **Configuración por tipo de negocio**: pizzería, heladería, restaurante, etc.
- Templates de setup inicial según el tipo
- Datos completamente separados por tenant

### 2. Configuración Flexible de Productos
- **Menús personalizables** por tipo de negocio
- **Categorías adaptables**: 
  - Pizzería: pizzas, bebidas, postres
  - Heladería: helados, batidos, tortas
  - Restaurante: entradas, platos principales, postres
- **Gestión de variantes**: tamaños, sabores, extras
- **Precios dinámicos** por categoría/horario

### 3. Control de Inventario Universal
- **Ingredientes base configurables**
  - Pizzería: harina, queso, tomate
  - Heladería: leche, azúcar, frutas
  - Restaurante: carnes, verduras, especias
- **Recetas y costos** por producto
- **Proveedores** y órdenes de compra
- **Stock mínimo** con alertas automáticas

### 4. Gestión de Personal + Reloj Biométrico
- **Empleados con roles**: cocinero, cajero, delivery, etc.
- **Turnos y horarios** flexibles por negocio
- **Integración futura**: API para relojes biométricos
- **Control de asistencia** automático
- **Cálculo de sueldos** con horas trabajadas + extras

### 5. Ventas Multi-Canal
- **POS integrado** para caja registradora
- **Formas de pago**: efectivo, tarjeta, QR, delivery apps
- **Comandas** para cocina/producción
- **Delivery tracking** básico
- **Promociones** y descuentos configurables

### 6. Contabilidad & Reportes
- **Dashboard por tipo de negocio** con KPIs relevantes
- **Reportes específicos**: 
  - Pizzería: pizzas más vendidas, horarios pico
  - Heladería: sabores populares, stock crítico
- **Integración contable** básica (ingresos/egresos)
- **Exportación** para contador externo

## 🏗️ Arquitectura Técnica ACTUALIZADA

### Apps Django Revisadas
1. **accounts** - Usuario, autenticación, tenants, **configuración de negocio**
2. **products** - Productos, menús, categorías **configurables**
3. **inventory** - Ingredientes, recetas, stock, proveedores
4. **sales** - Ventas, POS, formas de pago, comandas
5. **employees** - Personal, horarios, **integración biométrico**
6. **accounting** - Contabilidad, reportes, dashboard
7. **integrations** - APIs externas (biométrico, delivery, etc.)

### Modelo de Configuración
```python
class BusinessType(models.Model):
    name = models.CharField(max_length=50)  # 'pizzeria', 'heladeria', etc.
    display_name = models.CharField(max_length=100)
    default_categories = models.JSONField()  # Templates iniciales
    
class Tenant(models.Model):
    name = models.CharField(max_length=100)
    business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE)
    config = models.JSONField()  # Configuraciones específicas
    # ... resto
```

### Integración Reloj Biométrico
```python
# Future integration
class BiometricDevice(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    api_endpoint = models.URLField()
    
class AttendanceRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    action = models.CharField(choices=[('IN', 'Check In'), ('OUT', 'Check Out')])
    device = models.ForeignKey(BiometricDevice, on_delete=models.SET_NULL, null=True)
```

## 🚀 Plan de Desarrollo ACTUALIZADO

### Fase 1: Core Multi-Tenant (2-3 semanas)
- [ ] Setup multi-tenant con configuración de negocio
- [ ] Autenticación y roles
- [ ] **Wizard de setup inicial** por tipo de negocio
- [ ] CRUD productos configurables
- [ ] Dashboard básico adaptativo

### Fase 2: POS & Ventas (2 semanas)  
- [ ] Sistema POS completo
- [ ] Gestión de comandas
- [ ] Formas de pago múltiples
- [ ] Reportes de ventas por tipo de negocio

### Fase 3: Inventario & Personal (2 semanas)
- [ ] Control de stock e ingredientes
- [ ] Gestión de empleados y turnos
- [ ] Cálculo de costos y sueldos
- [ ] Alertas automáticas

### Fase 4: Integraciones (2-3 semanas)
- [ ] **API para reloj biométrico** (cuando tengas el modelo)
- [ ] Integración delivery apps
- [ ] Webhooks para sistemas externos
- [ ] Backup automático

### Fase 5: Advanced Features
- [ ] Analytics avanzado
- [ ] App móvil para empleados
- [ ] Multi-sucursal por tenant
- [ ] Facturación electrónica

## 💡 Tipos de Negocio Soportados

### 🍕 Pizzería
- **Productos**: Pizzas (tamaños), bebidas, postres
- **Ingredientes**: Masa, salsas, quesos, fiambres
- **KPIs**: Pizzas/hora, ingredientes críticos, delivery time

### 🍦 Heladería  
- **Productos**: Helados (sabores, porciones), batidos, tortas
- **Ingredientes**: Leche, frutas, coberturas, conos
- **KPIs**: Sabores populares, stock crítico verano, rotación

### 🍽️ Restaurante
- **Productos**: Entradas, principales, postres, bebidas
- **Ingredientes**: Carnes, verduras, especias, vinos
- **KPIs**: Platos estrella, costos, tiempo cocina

### ☕ Cafetería
- **Productos**: Cafés, tés, sandwiches, pasteles
- **Ingredientes**: Granos, leches, panes, dulces
- **KPIs**: Consumo horario, productos frescos

## 🎯 MVP Target (Primera implementación)

**2 negocios piloto**: Tu amiga (pizzería) + cuñado (heladería)

**Success criteria**:
- Setup inicial específico por tipo
- Menús configurados automáticamente  
- Registro de ventas funcional
- Control básico de empleados
- Dashboards diferenciados

---

**🍕🍦 Target**: Sistema universal listo en 8-10 semanas para múltiples tipos de negocio gastronómico.