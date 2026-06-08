# Andina — Sistema de Pedidos

Aplicación web para gestión de inventario y pedidos de Andina Tienda de Tesoros.

## Cómo usar

1. Entrá a la app en Streamlit Cloud
2. En la pestaña **Inicio**: subí los 3 archivos
   - Export de productos de WooCommerce (CSV)
   - Export de ventas del mes (XLSX)  
   - Archivo de costos de proveedoras (XLSX)
3. Ajustá el forecast de ventas
4. En **Análisis**: revisá rankings y alertas
5. En **Pedidos**: seleccioná la proveedora, editá cantidades, descargá el PDF

## Archivos necesarios

| Archivo | Dónde exportarlo |
|---------|-----------------|
| Productos WooCommerce | WooCommerce → Productos → Exportar |
| Ventas del mes | WooCommerce → Pedidos → Exportar |
| Costos proveedoras | Archivo Excel de costos actualizados |

## Setup local (desarrollo)

```bash
pip install -r requirements.txt
streamlit run app.py
```
