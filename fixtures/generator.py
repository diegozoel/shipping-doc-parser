"""
Synthetic PDF Fixture Generator
================================
Generates shipping note PDFs with fictional data that replicate
the exact text structure of real documents. The ETL pipeline
extracts data using text patterns (regex), not coordinates,
so the generated PDFs must produce the same label order and
formatting when read by pdfplumber.

Usage:
    python -m fixtures.generator

Output:
    fixtures/generated/*.pdf  (6 files: 3 movements x 2 layouts)
"""

import random
import string
from pathlib import Path
from fpdf import FPDF

# ---------------------------------------------------------------------------
# Synthetic data pools
# ---------------------------------------------------------------------------

FAKE_COMPANIES = [
    "Nexora Electronics Ltd",
    "Veridian Manufacturing Inc",
    "Arcturus Systems GmbH",
    "Solaris Tech Pvt Ltd",
    "Kaelum Industries S.A.",
]

FAKE_CITIES = [
    ("AUSTIN", "US"),
    ("MUNICH", "DE"),
    ("SINGAPORE", "SG"),
    ("PUNE", "IN"),
    ("PENANG", "MY"),
]

FAKE_CONTACTS = [
    "Maria Torres Hernandez",
    "James Chen Wei",
    "Anika Patel Sharma",
    "Lars Eriksson Berg",
    "Yuki Tanaka Sato",
]

FAKE_APPROVERS = {
    "Celda / Proyecto": "Ana Laura Mendez Rios",
    "finanzas": "Roberto Carlos Vega Luna",
    "Trafico": "Diana Patricia Leal Cruz",
    "Inventario": "Carlos Eduardo Mora Salas",
    "Calidad": "Patricia Gomez Delgado",
    "Embarque": "Miguel Angel Ruiz Torres",
}

CARRIERS = {
    "DHL": "C501-DHL EXPRESS MEXICO SA DE CV",
    "FedEx": "C017-FEDERAL EXPRESS HOLDINGS MEXICO Y CIA. S.N.C. DE C.V.",
    "UPS": "C230-UNITED PARCEL SERVICE DE MEXICO SA DE CV",
    "Special": "N/A-N/A",
}

PACKAGING_TYPES = ["BULK", "PALLET", "BOX"]

PART_PREFIXES = ["NXR", "VRD", "ARC", "SLR", "KLM"]
PART_CATEGORIES = ["IC", "HZ", "CR", "IN", "CP"]

DESCRIPTIONS = [
    "CAPACITOR,CERAMIC,100NF,50V,0402,X7R",
    "RESISTOR,THICK FILM,10K OHM,0603,1%",
    "INDUCTOR,FERRITE,4.7UH,0805,20%",
    "TRANSISTOR,MOSFET,N-CH,30V,SOT-23",
    "IC,VOLTAGE REGULATOR,3.3V,SOT-223",
    "DIODE,SCHOTTKY,40V,200MA,SOD-323",
    "CRYSTAL,QUARTZ,32.768KHZ,SMD",
    "FILTER,SAW,2.4GHZ,50OHM,SMD",
    "CONNECTOR,USB-C,24PIN,SMD",
    "LED,WHITE,0603,3.0V,20MA",
]


# ---------------------------------------------------------------------------
# Data generation helpers
# ---------------------------------------------------------------------------

def _random_shipper_id(prefix="NXR"):
    """Format: PREFIX + YYMM + DD + 4-digit seq + 'S'"""
    yy = random.randint(24, 26)
    mm = random.randint(1, 12)
    dd = random.randint(1, 28)
    seq = random.randint(1000, 9999)
    return f"{prefix}{yy:02d}{mm:02d}{dd:02d}{seq}S"


def _random_part_number():
    """Format: XXX-YY######A## (e.g., NXR-IC004512A01)"""
    prefix = random.choice(PART_PREFIXES)
    cat = random.choice(PART_CATEGORIES)
    num = random.randint(100, 999999)
    rev = random.randint(1, 15)
    return f"{prefix}-{cat}{num:06d}A{rev:02d}"


def _random_delivery():
    """9-digit delivery number."""
    return str(random.randint(800000000, 899999999))


def _random_qty():
    return random.randint(100, 50000)


def _random_cost():
    return round(random.uniform(0.001, 35.0), 5)


def _generate_items(count=10):
    """Generate a list of synthetic line items."""
    items = []
    for _ in range(count):
        qty = _random_qty()
        cost = _random_cost()
        items.append({
            "part": _random_part_number(),
            "qty": qty,
            "tx": _random_delivery(),
            "us": _random_delivery(),
            "cost": cost,
            "total": round(qty * cost, 5),
            "desc": random.choice(DESCRIPTIONS),
            "po": str(random.randint(100000000, 199999999)),
            "so": "".join(random.choices(string.ascii_uppercase + string.digits, k=10)),
            "so_us": str(random.randint(7000000000, 7099999999)),
            "so_tx": str(random.randint(7000000000, 7099999999)),
        })
    return items


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

class ShippingNotePDF(FPDF):
    """Generates a synthetic shipping note PDF."""

    def __init__(self, shipper_id, movement, layout, carrier_key, items):
        super().__init__()
        self.shipper_id = shipper_id
        self.movement = movement
        self.layout = layout
        self.carrier_key = carrier_key
        self.carrier_line = CARRIERS[carrier_key]
        self.items = items
        self.pkg_type = random.choice(PACKAGING_TYPES)
        self.company = random.choice(FAKE_COMPANIES)
        self.city, self.country = random.choice(FAKE_CITIES)
        self.contact = random.choice(FAKE_CONTACTS)
        self.set_auto_page_break(auto=True, margin=20)

    def _write_line(self, text):
        """Write a single line of text (font already set by caller)."""
        self.cell(0, 5, text, ln=True)

    def _write_doc_footer(self):
        """Standard legal footer present on every page of real documents."""
        self.ln(3)
        self.set_font("Helvetica", "I", 6)
        self._write_line(
            "DOCUMENTO EXPEDIDO PARA TRANSPORTAR MERCANCIAS POR EL "
            "TERRITORIO NACIONAL DE CONFORMIDAD CON LA REGLA 2.7.1.9. "
            "DE LA RESOLUCION MISCELANEA FISCAL VIGENTE"
        )

    def _write_page_header(self):
        """Repeated header block at the top of every page."""
        self.set_font("Helvetica", "B", 9)
        self._write_line(f"Nota de Embarque Shipper: {self.shipper_id}")
        self.set_font("Helvetica", "", 7)
        self._write_line(
            "EXPORTADOR: ACME MANUFACTURING DE MEXICO S. DE R.L. DE C.V."
        )
        self._write_line(
            "AV. INDUSTRIA NO.100, PARQUE INDUSTRIAL, C.P. 45010 "
            "ZAPOPAN, JAL. MEXICO / R.F.C.: ACM0001015QQ0 "
            "PROG. MAQUILA: IMMEX 0000-2000"
        )

    # ------------------------------------------------------------------
    # Page 1: Header / metadata
    # ------------------------------------------------------------------
    def build_header_page(self):
        self.add_page()
        self._write_page_header()

        self.set_font("Helvetica", "", 8)

        date_str = "Jan 15 2026"
        self._write_line(
            f"Estado: Listo para embarcar "
            f"Fecha de la Requisici\u00f3n: {date_str}"
        )
        self._write_line(
            f"Usuario Requisitor: {self.contact} "
            f"Tiene Activo Fijo:"
        )
        # Movement line — matched by main.py regex:
        # r"(?:Movement|Movimiento):\s*\n?\s*<CODE>"
        self._write_line(
            f"Movimiento: {self.movement} "
            f"N\u00famero de Activo:"
        )
        self._write_line(
            "Tipo de Requisici\u00f3n: Mixed "
            "Tipo de Movimiento: Consignaci\u00f3n"
        )
        self._write_line("Planta:TX02")
        self._write_line("Raz\u00f3n del Embarque")
        self._write_line("Razon: N/A")
        self._write_line("Informaci\u00f3n Adicional:")

        # Ship-to / Bill-to
        self._write_line("Enviar A Facturar A")
        self._write_line(
            f"Compa\u00f1ia: {self.company} "
            f"Compa\u00f1ia: {self.company}"
        )
        self._write_line(
            f"Ciudad: {self.city} Ciudad: {self.city}"
        )
        self._write_line(
            f"Pa\u00eds: {self.country} Pa\u00eds: {self.country}"
        )
        self._write_line(
            f"Direcci\u00f3n: Industrial Park 100 {self.city} 00000 "
            f"Direcci\u00f3n: Industrial Park 100 {self.city} 00000"
        )
        self._write_line("TaxID VAT: 000000000 TaxID VAT: 000000000")
        self._write_line(
            "C\u00f3digo ZOE: M00000 C\u00f3digo ZOE: M00000"
        )
        self._write_line("IMMEX: 0 IMMEX: 0")
        self._write_line(
            f"Retorno del Material: N/A "
            f"Nombre de Contacto: {self.contact}"
        )
        self._write_line(
            f"Nombre de Contacto: {self.contact} "
            f"Tel\u00e9fono: 0000000000"
        )
        self._write_line("Tel\u00e9fono: 0000000000")

        # Carrier line — base.py reads this with:
        # r"Transportista:\s*(.*)"
        self._write_line(
            f"Transportista: {self.carrier_line} "
            f"Inco Term: EXW"
        )
        self._write_line("Tipo de Transporte: Air Flete: Collected")
        self._write_line(
            "Tipo de Servicio: Standard Facturaci\u00f3n a Tercero"
        )
        self._write_line("Modo: Courier N\u00famero de Cuenta:")
        self._write_line(
            "N\u00famero de Cuenta: n/a Nombre de Compa\u00f1ia:"
        )
        self._write_line("PTA: Nombre de Contacto:")
        self._write_line(
            "Centro de Costos (Proyecto Requisitor): SYNTHETIC LINES "
            "C\u00f3digo CC: 0000000000"
        )
        self._write_line("Proveedor: N/A")
        self._write_line(
            "Tiene Debit Memo Certificado de Destrucci\u00f3n"
        )
        self._write_line("Comentarios: COO: SYNTHETIC")

        # Signatures
        self._write_line("Firmas")
        self._write_line(
            "Rol Projecto Usuarios Aprovadores Fecha de Firma"
        )
        project_name = "SYNTHETIC"
        for role, approver in FAKE_APPROVERS.items():
            self._write_line(
                f"{role} {project_name} {approver} "
                f"01/15/2026 9:00:00 AM"
            )

        # Bultos — base.py reads packaging type with:
        # r"Bultos[\s\S]*?(BULK|PALLET|BOX)"
        self._write_line("Bultos")
        self._write_line(
            "Tipo Cantidad Largo Ancho Alto Peso Cantidad de Cajas"
        )
        self._write_line(
            f"{self.pkg_type} 1 120.00 80.00 100.00 250.00 10"
        )

        self._write_doc_footer()

    # ------------------------------------------------------------------
    # Simple layout item pages
    # ------------------------------------------------------------------
    def build_simple_items_page(self):
        self.add_page()
        self._write_page_header()

        self.set_font("Helvetica", "B", 8)
        # "Items - Mixed" triggers first condition of detect_layout()
        self._write_line("Items - Mixed")

        # Column header line — the combined string
        # "Cantidad: Número de Parte:" triggers second condition
        self._write_line("Costo Val. agregado/")
        self._write_line(
            "Cantidad: N\u00famero de Parte: Delivery TX: Delivery US: "
            "PO TX: PO US: P/B: Descripci\u00f3n:"
        )
        self._write_line("unitario: Costo de rep:")

        self.set_font("Helvetica", "", 8)

        # Item rows — must match regex:
        # r"(\d+)\s+([A-Z0-9-]+)\s+(\d{9})\s+(\d{9})"
        for item in self.items:
            line = (
                f"{item['qty']} "
                f"{item['part']} "
                f"{item['tx']} "
                f"{item['us']} "
                f"{item['po']} "
                f"{item['cost']} "
                f"0 0/0 "
                f"{item['desc']}"
            )
            self._write_line(line)

        grand_total = sum(i["total"] for i in self.items)
        self._write_line(f"Importe Total: {grand_total}")

        self._write_doc_footer()

    # ------------------------------------------------------------------
    # Full layout item pages
    # ------------------------------------------------------------------
    def build_full_items_pages(self):
        self.add_page()
        self._write_page_header()

        self.set_font("Helvetica", "B", 8)
        self._write_line("Items - Mixed")
        self.set_font("Helvetica", "", 7)

        for item in self.items:
            # Check remaining space — add new page if needed
            if self.get_y() > 240:
                self._write_doc_footer()
                self.add_page()
                self._write_page_header()
                self.set_font("Helvetica", "", 7)

            # Each block starts with "Tipo de PO:" — the split delimiter
            # used by: re.split(r"Tipo de PO:", text)[1:]
            self._write_line("Tipo de PO: Entrega: Battery: No")
            self._write_line(
                f"PO: {item['po']} Cantidad: {item['qty']}"
            )
            self._write_line("Battery type: N/A")
            self._write_line(
                f"SO: {item['so']} Costo Unitario: {item['cost']}"
            )
            self._write_line(
                f"PO US: Costo Estandar: {item['cost']}"
            )
            self._write_line("Battery weight: N/A")
            self._write_line(
                f"PO TX: null Importe Total: {item['total']}"
            )
            self._write_line("Tipo de PO MRO: Carga:")
            self._write_line("PO MRO: Valor Agregado: 0")
            self._write_line(f"Orden Interno: SO US: {item['so_us']}")

            # CRITICAL: "Número de Parte:" must have accent (\u00fa = ú)
            # Matched by: r"Número de Parte:\s+([A-Z0-9-]+)"
            self._write_line(
                f"N\u00famero de Parte: {item['part']} N.P. Cliente:"
            )
            self._write_line(
                f"Vendedor: N/A Delivery US: {item['us']}"
            )
            self._write_line(
                f"C\u00f3digo Vendedor: 0 Delivery TX: {item['tx']}"
            )
            self._write_line(
                f"SO TX: {item['so_tx']} Unidad de Medida:"
            )
            self._write_line(
                "RMA: Descripci\u00f3n (En): ELECTRONIC COMPONENTS"
            )
            self._write_line(f"Descripci\u00f3n (Es): {item['desc']}")
            self.ln(2)

        grand_total = sum(i["total"] for i in self.items)
        self._write_line(f"Importe Total: {grand_total}")

        self._write_doc_footer()

    # ------------------------------------------------------------------
    # Last page: carrier signature form (always blank)
    # ------------------------------------------------------------------
    def build_carrier_page(self):
        self.add_page()
        self._write_page_header()
        self.set_font("Helvetica", "", 8)
        self._write_line("Transportista")
        self._write_line("Fecha:_____/_____/______ Hora:____:____")
        self._write_line(
            "Nombre del Chofer:________________________________ "
            "Transportista:___________________________________"
        )
        self._write_line(
            "Direcci\u00f3n:"
            "____________________________________________________________"
            "_________________________"
        )
        self._write_line(
            "# Unidad:________________________________ "
            "N\u00famero econ\u00f3mico:____________________________________"
        )
        self._write_line("Placas:__________________________________")
        self._write_line("______________________________________________")
        self._write_line("Sellos")
        self._write_line("Firma")
        self._write_doc_footer()

    # ------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------
    def build(self):
        self.build_header_page()
        if self.layout == "Simple":
            self.build_simple_items_page()
        else:
            self.build_full_items_pages()
        self.build_carrier_page()


# ---------------------------------------------------------------------------
# Configuration: 3 movements x 2 layouts = 6 PDFs, 10 items each
# ---------------------------------------------------------------------------

CONFIGURATIONS = [
    {"movement": "601", "layout": "Full", "carrier": "DHL"},
    {"movement": "601", "layout": "Simple", "carrier": "Special"},
    {"movement": "643", "layout": "Full", "carrier": "FedEx"},
    {"movement": "643", "layout": "Simple", "carrier": "UPS"},
    {"movement": "Z61", "layout": "Full", "carrier": "FedEx"},
    {"movement": "Z61", "layout": "Simple", "carrier": "DHL"},
]

ITEMS_PER_PDF = 10


def generate_all():
    """Generate all synthetic fixture PDFs."""
    output_dir = Path(__file__).parent / "generated"
    output_dir.mkdir(exist_ok=True)

    random.seed(42)  # Reproducible outputs

    for config in CONFIGURATIONS:
        mov = config["movement"]
        layout = config["layout"]
        carrier = config["carrier"]

        prefix = random.choice(PART_PREFIXES)
        shipper_id = _random_shipper_id(prefix)
        items = _generate_items(ITEMS_PER_PDF)

        pdf = ShippingNotePDF(
            shipper_id=shipper_id,
            movement=mov,
            layout=layout,
            carrier_key=carrier,
            items=items,
        )
        pdf.build()

        filename = f"{mov}_{layout.lower()}_sample.pdf"
        filepath = output_dir / filename
        pdf.output(str(filepath))
        print(f"Generated: {filepath.name} ({ITEMS_PER_PDF} items, {carrier})")

    print(f"\nAll fixtures generated in: {output_dir}")


if __name__ == "__main__":
    generate_all()
