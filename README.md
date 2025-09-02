[![License: AGPL-3](https://img.shields.io/badge/licence-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0.html)
[![Build Status](https://travis-ci.org/odoo-dominicana/l10n-dominicana.svg?branch=16.0-pro)](https://travis-ci.org/odoo-dominicana/l10n-dominicana)
[![codecov](https://codecov.io/gh/odoo-dominicana/l10n-dominicana/branch/16.0/graph/badge.svg)](https://codecov.io/gh/odoo-dominicana/l10n-dominicana)

# Localización RD para Facturación Fiscal

Este repositorio consolida los módulos utilizados para poder realizar facturación en República Dominicana desde los módulos de Ventas, Contable y Punto de Ventas.

Principalmente se enfoca en la gestión de los Números de Comprobantes Fiscal (**NCF**) y facilita ciertas funcionalidades para el uso de los mismos como:
- Secuencias **Preconfiguradas** para manejo de todos los NCF
   - Facturas con Valor Fiscal (para Ventas)
   - Facturas para Consumidores Finales
   - Gubernamentales
   - Regímenes Especiales
   - Comprobante para Exportaciones
   - Notas de Débito y Crédito
   - Registro de Ingreso Único
   - Comprobantes de Compras
   - Registro de Gastos Menores
   - Pagos al Exterior

- Validación en **tiempo real** de comprobantes
	- Estructura correcta del NCF digitado
	- Validación de relación **NCF-RNC** con WebService de DGII

- Creación de contactos por **RNC** o **Cédula**
	- Consulta con el WebService de DGII

- Emisión de Facturas Fiscales desde el **Punto de Venta**

## 📦 Módulos Incluidos

### [l10n_do_ncf](l10n_do_ncf/) - Contabilidad Fiscal
**Gestión completa de Números de Comprobantes Fiscales (NCF)**
- Administración automática de secuencias NCF
- Validación en tiempo real con DGII
- Soporte para todos los tipos de NCF (01-17)
- Integración con módulo de contabilidad

### [l10n_do_dgii_reports](l10n_do_dgii_reports/) - Reportes DGII
**Generación de reportes fiscales para DGII**
- Reportes 606, 607, 608, 609, IT-1
- Exportación en formatos oficiales de DGII
- Validación de datos fiscales
- Clasificación automática de transacciones

### [l10n_do_pos](l10n_do_pos/) - Punto de Venta Fiscal
**Facturación fiscal desde el Punto de Venta**
- Emisión de NCF en tiempo real
- Interfaz POS adaptada para requisitos fiscales
- Soporte para múltiples tipos de pago
- Integración con impresoras fiscales

### [l10n_do_rnc](l10n_do_rnc/) - Búsqueda por RNC
**Consulta automática de información empresarial**
- Búsqueda de razón social por RNC
- Validación en tiempo real con DGII
- Auto-completado de información de contactos
- Soporte para múltiples servicios de consulta

## 🚀 Instalación Rápida


1. **Instalación de módulos**:
   - Copiar el repositorio a la carpeta de addons de Odoo
   - Actualizar lista de aplicaciones
   - Instalar módulos en el siguiente orden:
     1. `l10n_do_ncf` (Contabilidad Fiscal)
     2. `l10n_do_dgii_reports` (Reportes DGII)
     3. `l10n_do_pos` (POS Fiscal - opcional)
     4. `l10n_do_rnc` (Búsqueda RNC - opcional)

2. **Configuración inicial**:
   - Configurar información fiscal de la empresa (RNC)
   - Establecer secuencias NCF en diarios
   - Configurar tipos de impuestos dominicanos
   - Probar integración con servicios DGII

## 📋 Guía de Uso

### Configuración Básica
1. **Empresa**: Configurar RNC y datos fiscales
2. **Diarios**: Asignar secuencias NCF apropiadas
3. **Clientes**: Configurar RNC/Cédula de clientes
4. **Productos**: Clasificar productos según normativa fiscal

### Operaciones Diarias
1. **Facturas de Venta**: NCF automático según tipo de cliente
2. **Facturas de Compra**: Validación de NCF de proveedores
3. **Punto de Venta**: Emisión fiscal en tiempo real
4. **Reportes**: Generación mensual de reportes DGII

## 🔍 Validaciones y Cumplimiento

- ✅ Validación de formato NCF
- ✅ Verificación de secuencias autorizadas
- ✅ Integración con servicios web DGII
- ✅ Cumplimiento con normativa 06-18
- ✅ Soporte para auditorías fiscales

## Contribuciones

Antes de hacer una contribución al repositorio a través de un PR, les recomendamos pasar por el [historial de commits de Odoo](https://github.com/odoo/odoo/commits/11.0) donde podrán visualizar el esquema el cual seguirá este repositorio.

También, antes de cualquier publicación deben leer la [guía de Contribución de OCA](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst) que es la base de nuestras políticas de contribución.

> Antes de poder hacer una contribución, si es la primera que realizas, debes crear un **issue** explicando el problema e indicando que harás un **PR**.
>
> 
