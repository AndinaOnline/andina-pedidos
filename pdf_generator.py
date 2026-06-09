"""
PDF generator for Andina purchase orders.
Uses fpdf2 to create branded PDFs with product data.
"""
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import requests
from io import BytesIO

ROSA = (251, 219, 219)
ARENA = (223, 206, 192)
NEGRO = (0, 0, 0)

# Sanitiza texto a latin-1 (fuente core Helvetica). Evita crashes por comillas
# tipográficas, guiones largos, etc. que pueden venir en nombres de WooCommerce.
_REPL = {'\u2014': '-', '\u2013': '-', '\u2018': "'", '\u2019': "'",
         '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2022': '-', '\u00a0': ' '}
def _s(text) -> str:
    t = str(text) if text is not None else ''
    for k, v in _REPL.items():
        t = t.replace(k, v)
    return t.encode('latin-1', 'replace').decode('latin-1')
GRIS = (96, 96, 96)
BLANCO = (255, 255, 255)
VERDE_AGUA = (234, 237, 232)


class AndinaPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Black header bar
        self.set_fill_color(*NEGRO)
        self.rect(0, 0, 210, 28, 'F')
        # Andina logo (versión rosa sobre barra negra). Fallback a texto si falta.
        import os
        logo = os.path.join(os.path.dirname(__file__), 'assets', 'andina_logo_rosa.png')
        try:
            self.image(logo, x=15, y=7, h=14)
        except Exception:
            self.set_xy(15, 8)
            self.set_font('Helvetica', 'I', 20)
            self.set_text_color(*ROSA)
            self.cell(80, 12, 'Andina', ln=False)
        # Right side subtitle
        self.set_xy(110, 10)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*ARENA)
        self.cell(85, 6, 'ORDEN DE PEDIDO', align='R', ln=True)
        self.set_xy(110, 16)
        self.set_font('Helvetica', '', 8)
        self.cell(85, 5, 'www.andinaonline.com.ar', align='R')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*GRIS)
        self.cell(0, 5, f'Andina - Tienda de Tesoros  |  Pág. {self.page_no()}', align='C')

    def order_info(self, proveedor: str, fecha: str, total_unidades: int, total_ars: float):
        # Info box
        self.set_fill_color(*VERDE_AGUA)
        self.set_draw_color(*ARENA)
        self.rect(15, self.get_y(), 180, 20, 'FD')
        y = self.get_y() + 4
        self.set_xy(20, y)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*NEGRO)
        self.cell(40, 5, 'Proveedora:', ln=False)
        self.set_font('Helvetica', '', 10)
        self.cell(60, 5, proveedor, ln=False)
        self.set_font('Helvetica', 'B', 10)
        self.cell(30, 5, 'Fecha:', ln=False)
        self.set_font('Helvetica', '', 10)
        self.cell(40, 5, fecha)
        self.ln(6)
        self.set_x(20)
        self.set_font('Helvetica', 'B', 10)
        self.cell(40, 5, 'Total unidades:', ln=False)
        self.set_font('Helvetica', '', 10)
        self.cell(60, 5, str(total_unidades), ln=False)
        self.set_font('Helvetica', 'B', 10)
        self.cell(30, 5, 'Total ARS:', ln=False)
        self.set_font('Helvetica', '', 10)
        self.cell(40, 5, f'${total_ars:,.0f}' if total_ars > 0 else '-')
        self.ln(12)

    def table_header(self):
        self.set_fill_color(*NEGRO)
        self.set_text_color(*BLANCO)
        self.set_font('Helvetica', 'B', 8)
        cols = [('SKU Andina', 24), ('Nombre', 48), ('SKU Prov.', 26),
                ('Desc. Proveedora', 34), ('Cant.', 14), ('Precio', 18), ('Subtotal', 16)]
        for label, w in cols:
            self.cell(w, 7, label, border=0, fill=True)
        self.ln()

    def table_row(self, sku, nombre, sku_prov, desc_prov, cant, precio, subtotal, shade=False):
        self.set_fill_color(*(VERDE_AGUA if shade else BLANCO))
        self.set_text_color(*GRIS)
        self.set_font('Helvetica', '', 8)
        y_start = self.get_y()
        # Draw cells
        self.cell(24, 6, str(sku)[:12], fill=True)
        self.cell(48, 6, str(nombre)[:30], fill=True)
        self.cell(26, 6, str(sku_prov)[:16], fill=True)
        self.cell(34, 6, str(desc_prov)[:22], fill=True)
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(*NEGRO)
        self.cell(14, 6, str(cant), align='C', fill=True)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*GRIS)
        precio_str = f'${precio:,.0f}' if precio and precio > 0 else '-'
        sub_str = f'${subtotal:,.0f}' if subtotal and subtotal > 0 else '-'
        self.cell(18, 6, precio_str, align='R', fill=True)
        self.cell(16, 6, sub_str, align='R', fill=True)
        # Bottom border
        self.set_draw_color(*ARENA)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln()

    def total_row(self, total_unidades, total_ars):
        self.ln(3)
        self.set_fill_color(*NEGRO)
        self.set_text_color(*BLANCO)
        self.set_font('Helvetica', 'B', 9)
        self.set_x(15)
        self.cell(132, 8, 'TOTAL DEL PEDIDO', fill=True)
        self.cell(14, 8, str(total_unidades), align='C', fill=True)
        self.cell(18, 8, '', fill=True)
        total_str = f'${total_ars:,.0f}' if total_ars > 0 else '-'
        self.cell(16, 8, total_str, align='R', fill=True)
        self.ln()


def generate_pdf(pedido_df: pd.DataFrame, proveedor: str, edited_qtys: dict = None) -> bytes:
    """
    Generate PDF for a single provider's order.
    pedido_df: filtered dataframe with columns SKU, Nombre, SKU_Prov, Nombre_Prov, Costo_ARS, Pedido_propuesto
    edited_qtys: {sku: qty} overrides from user
    """
    pdf = AndinaPDF()
    pdf.add_page()
    
    fecha = datetime.now().strftime('%d/%m/%Y')
    
    rows_data = []
    total_u = 0
    total_ars = 0.0
    
    for _, row in pedido_df.iterrows():
        sku = row['SKU']
        qty = edited_qtys.get(sku, int(row.get('Pedido_propuesto', 0))) if edited_qtys else int(row.get('Pedido_propuesto', 0))
        if qty <= 0:
            continue
        costo = row.get('Costo_ARS', None)
        subtotal = qty * costo if (costo and not pd.isna(costo)) else None
        rows_data.append({
            'sku': _s(sku),
            'nombre': _s(str(row.get('Nombre', ''))[:32]),
            'sku_prov': _s(str(row.get('SKU_Prov', '') or '')),
            'desc_prov': _s(str(row.get('Nombre_Prov', '') or '')),
            'qty': qty,
            'precio': costo if costo and not pd.isna(costo) else None,
            'subtotal': subtotal,
        })
        total_u += qty
        if subtotal: total_ars += subtotal
    
    pdf.order_info(_s(proveedor), fecha, total_u, total_ars)
    pdf.table_header()
    
    for i, r in enumerate(rows_data):
        pdf.table_row(
            r['sku'], r['nombre'], r['sku_prov'], r['desc_prov'],
            r['qty'], r['precio'], r['subtotal'], shade=(i % 2 == 0)
        )
    
    pdf.total_row(total_u, total_ars)
    
    # Footer note
    pdf.ln(8)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(0, 4, 
        'Este pedido fue generado por el sistema de gestión de inventario de Andina - Tienda de Tesoros. '
        'Las cantidades reflejan el pedido propuesto basado en ventas históricas y cobertura de stock. '
        'Ante cualquier consulta escribir a hola@andinaonline.com.ar')
    
    return bytes(pdf.output())
