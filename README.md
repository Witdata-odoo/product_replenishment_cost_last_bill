# Costo de Reposición desde Última Factura de Proveedor

Módulo para Odoo 18 que extiende `product_replenishment_cost` (ADHOC) con un nuevo método de cálculo del costo de reposición: **Última Factura de Proveedor** (`last_vendor_bill`).

## Dependencias

- `product_replenishment_cost`
- `account`

## Funcionamiento

### 1. Nuevo método de costeo

En la pestaña de compras del producto, el campo **Tipo de costo de reposición** (`replenishment_cost_type`) suma la opción **Last Vendor Bill**. Al seleccionarla:

- El costo base se toma de la última factura de proveedor posteada del producto.
- Se aplica la **regla de costo de reposición** del producto (si tiene), igual que en los demás métodos.
- Si se desinstala el módulo, los productos con este método vuelven a `Manual`.

### 2. Cálculo del costo de reposición

Se busca la última línea de producto de una factura de proveedor (`in_invoice`) que cumpla:

- Factura en estado **posteada**.
- Misma **compañía** que la compañía activa.
- Producto igual al del template (el módulo trabaja a nivel `product.template`, sin distinción de variantes).
- Orden por **fecha de factura** (`invoice_date`) descendente; ante empate, la más reciente por id.

El precio se calcula así:

- `price_unit` de la línea menos el **descuento de línea** (`discount`).
- **Sin impuestos.**
- En la **moneda de la factura**; luego se convierte a la moneda del producto con la lógica nativa del módulo base.
- Si la unidad de medida de la línea difiere de la de compra del producto, se convierte a la unidad de medida de compra, igual que en los demás métodos del módulo base.

Si no existe ninguna factura posteada para el producto, el costo de reposición es **$0.00**.

### 3. Actualización del Costo Contable

El módulo sobrescribe `account.move._post()`. Cada vez que se postea una factura de proveedor:

1. Se filtran las líneas de producto de la factura.
2. Se identifican los productos cuyo `replenishment_cost_type` sea `last_vendor_bill`.
3. Sobre esos productos se ejecuta `_update_cost_from_replenishment_cost()`, que actualiza directamente el `standard_price`.

Esto significa que, **solo para este método**, el Costo Contable se actualiza en el momento de confirmar la factura, sin pasar por el wizard manual ("Update Accounting Cost from Replenishment Cost") ni por el cron.

Igualmente, el wizard y el cron del módulo base (inactivo por defecto) siguen funcionando con este método y toman la última factura vigente. No se realiza ningún recálculo inicial al instalar el módulo.

> **Atención:** si la empresa usa valuación de inventario automática, cada actualización de `standard_price` genera asientos de valuación.

### 4. Casos que NO afectan el costo

- **Facturas en borrador**: se ignoran hasta que se postean.
- **Notas de crédito** (`in_refund`): se ignoran.
- **Facturas posteadas con `invoice_date` anterior** a la última considerada: aunque se posteen después, si su fecha de factura es más antigua no reemplazan el costo vigente. El criterio es siempre `invoice_date`, nunca el orden de posteo.
- **Cambio de tipo de costeo**: si el producto deja de usar `last_vendor_bill` (por ejemplo, se cambia a "Manual"), deja de reaccionar a nuevas facturas.

## Pruebas realizadas

Se validó el comportamiento manualmente en una base Odoo 18 con los siguientes casos (relacionados con los tests automatizados `test_no_bill_is_zero`, `test_last_bill_by_invoice_date`, `test_discount_and_draft_ignored`, `test_other_type_unaffected`):

| # | Escenario | Resultado esperado | Resultado obtenido |
|---|---|---|---|
| 1 | Producto sin facturas | Costo = $0.00 | ✅ $0.00 |
| 2 | Factura directa posteada ($20) | Costo Contable se actualiza solo | ✅ $20.00, sin wizard |
| 3 | Flujo OC → Recepción → Factura ($45, 20% desc.) | Costo = 45 × 0.8 = $36 | ✅ $36.00 automático |
| 4 | Factura con fecha anterior posteada después | No reemplaza el costo vigente | ✅ sin cambios ($36) |
| 5 | Factura en borrador | Se ignora | ✅ sin cambios |
| 6 | Cambio a tipo "Manual" + nueva factura posteada | No reacciona | ✅ sin cambios |

## Notas técnicas

- El método respeta multiempresa (`with_company`) y filtra las facturas por compañía.
- El cálculo busca una línea por producto; para lotes grandes vía cron puede ser más lento que los otros métodos.
- El descuento global de la factura no se considera, solo el descuento de línea.

## Autor

Desarrollado por WITDATA.
