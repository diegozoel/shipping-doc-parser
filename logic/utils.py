import re


def clean_text(text):
    if not text:
        return ""
    # Removes double spaces, newlines and strips ends
    return " ".join(text.split()).strip()


def extract_regex_value(pattern, text, group_index=1):
    # Standardizing regex search with IGNORECASE to avoid template variations
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(group_index) if match else None


def detect_layout(all_text):
    """Determines if a shipping note uses Simple or Full layout."""
    is_simple = "Items - Mixed" in all_text and "Cantidad: Número de Parte:" in all_text
    return "Simple" if is_simple else "Full"
