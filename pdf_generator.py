"""
PDF generator for Andina purchase orders.
Uses fpdf2 to create branded PDFs with product data.
"""
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import requests
from io import BytesIO

_IMG_CACHE = {}
def _fetch_img_bytes(url):
    """Descarga la foto del producto y la devuelve como PNG en bytes (cacheada).
    Si falla (sin red, URL inválida), devuelve None y el PDF sigue sin imagen."""
    if not (isinstance(url, str) and url.startswith('http')):
        return None
    if url in _IMG_CACHE:
        return _IMG_CACHE[url]
    try:
        r = requests.get(url, timeout=6)
        r.raise_for_status()
        from PIL import Image
        im = Image.open(BytesIO(r.content)).convert('RGB')
        im.thumbnail((200, 200))
        buf = BytesIO()
        im.save(buf, 'PNG')
        _IMG_CACHE[url] = buf.getvalue()
    except Exception:
        _IMG_CACHE[url] = None
    return _IMG_CACHE[url]

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
        cols = [('Foto', 20), ('SKU', 20), ('Nombre', 40), ('SKU Prov.', 24),
                ('Desc. Proveedora', 30), ('Cant.', 12), ('Precio', 18), ('Subtotal', 16)]
        for label, w in cols:
            self.cell(w, 7, label, border=0, fill=True)
        self.ln()

    def table_row(self, img_bytes, sku, nombre, sku_prov, desc_prov, cant, precio, subtotal, shade=False):
        h = 16
        x0, y0 = 15, self.get_y()
        if y0 + h > 280:                      # salto de página
            self.add_page()
            self.table_header()
            y0 = self.get_y()
        self.set_fill_color(*(VERDE_AGUA if shade else BLANCO))
        self.rect(x0, y0, 180, h, 'F')
        if img_bytes:
            try:
                self.image(BytesIO(img_bytes), x=x0 + 2, y=y0 + 2, w=16, h=12)
            except Exception:
                pass

        def txt(x, w, s, align='L', bold=False, color=GRIS):
            self.set_xy(x, y0 + (h - 5) / 2)
            self.set_font('Helvetica', 'B' if bold else '', 8)
            self.set_text_color(*color)
            self.cell(w, 5, s, align=align)

        txt(35, 20, str(sku)[:11])
        txt(55, 40, str(nombre)[:32])
        txt(95, 24, str(sku_prov)[:14])
        txt(119, 30, str(desc_prov)[:20])
        txt(149, 12, str(cant), align='C', bold=True, color=NEGRO)
        txt(161, 18, f'${precio:,.0f}' if precio and precio > 0 else '-', align='R')
        txt(179, 16, f'${subtotal:,.0f}' if subtotal and subtotal > 0 else '-', align='R')

        self.set_draw_color(*ARENA)
        self.set_xy(x0, y0 + h)
        self.line(15, y0 + h, 195, y0 + h)

    def total_row(self, total_unidades, total_ars):
        self.ln(3)
        self.set_fill_color(*NEGRO)
        self.set_text_color(*BLANCO)
        self.set_font('Helvetica', 'B', 9)
        self.set_x(15)
        self.cell(134, 8, 'TOTAL DEL PEDIDO', fill=True)
        self.cell(12, 8, str(total_unidades), align='C', fill=True)
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
            'img': _fetch_img_bytes(row.get('Imagen_url', None)),
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
            r['img'], r['sku'], r['nombre'], r['sku_prov'], r['desc_prov'],
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
