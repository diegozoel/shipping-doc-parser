import pdfplumber
import pandas as pd
import re
import logging
from pathlib import Path
from logic import utils
from logic import move_601, move_643, move_z61
from logic.reporting import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("shipping_etl")

REQUIRED_FIELDS = {
    "601": ["Part Number", "Quantity", "Delivery TX", "Delivery US"],
    "643": ["Part Number", "Quantity", "Delivery TX", "Delivery US"],
    "Z61": ["Part Number", "Quantity", "Delivery TX", "Delivery US"],
}

def run_orchestrator():
    base_path = Path(__file__).parent
    input_dir = base_path / "data"
    output_dir = base_path / "output"
    output_dir.mkdir(exist_ok=True)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}.")
        return

    results_list = []
    success_log = []
    error_log = []

    for file_path in pdf_files:
        try:
            with pdfplumber.open(file_path) as pdf:
                all_text = ""
                for page in pdf.pages:
                    all_text += (page.extract_text() or "") + "\n"

                # PDF content validation
                if len(all_text.strip()) < 50:
                    error_log.append({
                        "file": file_path.name,
                        "error": f"PDF appears empty or unreadable ({len(all_text.strip())} chars extracted)"
                    })
                    continue

                header_text = pdf.pages[0].extract_text() or ""
                layout_type = utils.detect_layout(all_text)

                df_result = None
                move_type = "N/A"

                # Movement identification and routing
                if re.search(r"(?:Movement|Movimiento):\s*\n?\s*601", header_text, re.IGNORECASE):
                    move_type = "601"
                    df_result = move_601.process_extraction(pdf, file_path.name, layout=layout_type, text=all_text)

                elif re.search(r"(?:Movement|Movimiento):\s*\n?\s*643", header_text, re.IGNORECASE):
                    move_type = "643"
                    df_result = move_643.process_extraction(pdf, file_path.name, layout=layout_type, text=all_text)

                elif re.search(r"(?:Movement|Movimiento):\s*\n?\s*Z61", header_text, re.IGNORECASE):
                    move_type = "Z61"
                    df_result = move_z61.process_extraction(pdf, file_path.name, layout=layout_type, text=all_text)

                # Result logging
                if df_result is not None:
                    carrier_val = df_result['Carrier'].iloc[0] if 'Carrier' in df_result.columns else "N/A"

                    results_list.append(df_result)
                    success_log.append({
                        "file": file_path.name,
                        "move": move_type,
                        "layout": layout_type,
                        "items": len(df_result),
                        "carrier": carrier_val
                    })
                else:
                    error_log.append({
                        "file": file_path.name,
                        "error": "Movement pattern not found or extraction returned empty"
                    })

        except Exception as e:
            error_log.append({"file": file_path.name, "error": str(e)})

    # Data Consolidation
    final_df = pd.DataFrame()
    if results_list:
        final_df = pd.concat(results_list, ignore_index=True)
        index_cols = ["Shipper", "Carrier", "Type", "Mov.", "Part Number"]
        available_index = [col for col in index_cols if col in final_df.columns]
        if available_index:
            final_df.set_index(available_index, inplace=True)

        final_df.to_excel(output_dir / "Consolidated_Matrix.xlsx")

        for mov, group in final_df.groupby("Mov."):
            required = REQUIRED_FIELDS.get(mov, ["Part Number", "Quantity"])
            for col in required:
                if col in group.columns:
                    missing = group[col].isna().sum() + (group[col].astype(str).isin(["-", "0", ""]).sum())
                    if missing > 0:
                        logger.warning(f"Mov {mov}: {missing} rows missing '{col}'")

    # Final Validation
    total_items_reported = sum(item['items'] for item in success_log)
    total_items_in_df = len(final_df)

    if total_items_reported == total_items_in_df and total_items_reported > 0:
        logger.info(f"Integrity Check Passed: {total_items_in_df} total items consolidated.")
    elif total_items_reported != total_items_in_df:
        logger.warning(f"Integrity Mismatch: log={total_items_reported}, matrix={total_items_in_df}")
    else:
        logger.warning("No data was processed.")

    # Generate Sorted Report
    report_path = output_dir / "Execution_Report.pdf"
    generate_report(success_log, error_log, report_path)
    logger.info(f"Process finished. Report: {report_path.name}")


if __name__ == "__main__":
    run_orchestrator()
