import pandas as pd
import re
from logic import utils
from logic.base import extract_metadata, create_row_dict


def process_extraction(pdf_obj, filename, layout="Full", text=None):
    if text is None:
        all_text = ""
        for page in pdf_obj.pages:
            all_text += (page.extract_text() or "") + "\n"
    else:
        all_text = text

    metadata = extract_metadata(all_text, "601")

    if layout == "Simple":
        df = _handle_simple_layout(all_text, metadata)
    else:
        df = _handle_full_layout(all_text, metadata)

    if not df.empty:
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0).astype(int)
        df = df.sort_values(by='Quantity', ascending=True)

    return df


def _handle_simple_layout(text, metadata):
    items = []
    row_pattern = re.compile(r"(\d+)\s+([A-Z0-9-]+)\s+(\d{9})\s+(\d{9})")
    matches = row_pattern.findall(text)

    for match in matches:
        qty, part, tx, us = match
        items.append(create_row_dict(metadata, part, qty, tx, us))

    return pd.DataFrame(items)


def _handle_full_layout(text, metadata):
    items = []
    item_blocks = re.split(r"Tipo de PO:", text)[1:]

    for block in item_blocks:
        part = utils.extract_regex_value(r"Número de Parte:\s+([A-Z0-9-]+)", block)
        qty = utils.extract_regex_value(r"Cantidad:\s+(\d+)", block)
        tx = utils.extract_regex_value(r"Delivery TX:\s+(\d{9})", block)
        us = utils.extract_regex_value(r"Delivery US:\s+(\d{9})", block)

        if part:
            items.append(create_row_dict(
                metadata, part, qty or "0", tx or "-", us or "-"
            ))

    return pd.DataFrame(items)
