import re
from logic import utils


def extract_metadata(text, movement_code):
    """Extracts common metadata fields from shipping note text."""
    shipper = utils.extract_regex_value(r"Shipper:\s*\n?\s*(\w+)", text)

    raw_carrier = utils.extract_regex_value(r"Transportista:\s*(.*)", text) or ""

    if re.search(r"DHL", raw_carrier, re.IGNORECASE):
        carrier = "DHL"
    elif re.search(r"FedEx|Federal", raw_carrier, re.IGNORECASE):
        carrier = "FedEx"
    elif re.search(r"UPS|United", raw_carrier, re.IGNORECASE):
        carrier = "UPS"
    else:
        carrier = "Special"

    type_match = re.search(r"Bultos[\s\S]*?(BULK|PALLET|BOX)", text, re.IGNORECASE)
    packaging_type = type_match.group(1).upper() if type_match else "-"

    return {
        "Shipper": utils.clean_text(shipper) if shipper else "-",
        "Carrier": carrier,
        "Type": packaging_type,
        "Mov.": movement_code,
    }


def create_row_dict(metadata, part, qty, tx, us, po="-", rma="-"):
    """Returns a standardized dictionary for the final DataFrame."""
    return {
        "Shipper": metadata["Shipper"],
        "Carrier": metadata["Carrier"],
        "Type": metadata["Type"],
        "Mov.": metadata["Mov."],
        "Part Number": part,
        "Quantity": qty,
        "Delivery TX": tx,
        "Delivery US": us,
        "PO": po,
        "RMA": rma,
        "Requisitor": "",
        "Comentaries": "",
    }
