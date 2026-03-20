# Shipping Doc Parser

An ETL pipeline that extracts structured data from shipping note PDFs and consolidates it into a single Excel matrix. Built to replace a fully manual, copy-paste workflow in the logistics operations of a Fortune 500 electronics manufacturing company.

## The Problem

In high-volume shipping operations, outbound shipments generate PDF documents (shipping notes) containing critical data: part numbers, quantities, delivery references, carrier information, and packaging details. At the facility where this tool was developed, these documents were processed entirely by hand — operators copied data line by line from PDFs into spreadsheets across an area handling **$100M+ USD in annual transactions**.

This manual process had been in place for over five years with no formal solution. It was slow, error-prone, and scaled poorly as transaction volume grew.

## The Solution

Shipping Doc Parser automates the extraction end-to-end:

1. **Reads** shipping note PDFs using text extraction (not OCR or coordinate-based parsing)
2. **Identifies** the movement type and document layout automatically
3. **Extracts** item-level data using regex patterns matched against document labels
4. **Consolidates** all extracted data into a single structured Excel file
5. **Generates** an execution report with processing results and error tracking

The pipeline handles multiple SAP movement types (601, 643, Z61) and two distinct document layouts (Simple and Full) through a modular architecture designed to scale to additional movement types without structural refactoring.

## Architecture

```
main.py                     Orchestrator — routes PDFs to the correct module
logic/
├── base.py                 Shared extraction logic (metadata, row construction)
├── utils.py                Layout detection, text cleaning, regex helpers
├── reporting.py            Execution report generation (PDF)
├── move_601.py             Movement 601 extraction (Simple + Full)
├── move_643.py             Movement 643 extraction (Simple + Full)
└── move_z61.py             Movement Z61 extraction (Simple + Full)
fixtures/
├── generator.py            Synthetic PDF generator for testing
└── generated/              Pre-generated sample PDFs (ready to use)
```

**How extraction works:** The pipeline does not rely on absolute coordinates or visual parsing. Instead, it uses contextual text patterns — extracting values that follow known labels (e.g., the number after `"Cantidad:"`) and filtering noise from overlapping column text that `pdfplumber` reads in the same block. This makes the extraction resilient to minor layout variations across document versions.

**Layout detection:** Each shipping note uses one of two layouts. The `detect_layout()` function determines which one by checking for specific text markers in the document. Each movement module then delegates to the appropriate handler (`_handle_simple_layout` or `_handle_full_layout`).

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
git clone https://github.com/diegozoel/shipping-doc-parser.git
cd shipping-doc-parser
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run with Sample Data

The repository includes pre-generated synthetic PDFs so you can test the full pipeline immediately:

```bash
# Copy sample fixtures to the data directory
cp fixtures/generated/*.pdf data/

# Run the ETL pipeline
python3 main.py
```

**Output:**
- `output/Consolidated_Matrix.xlsx` — Structured matrix with all extracted data
- `output/Execution_Report.pdf` — Processing summary with success/error breakdown

### Regenerate Fixtures

To generate fresh synthetic PDFs (optional — samples are already included):

```bash
python3 -m fixtures.generator
```

This produces 6 PDFs (3 movement types × 2 layouts) with 10 items each, using fictional companies, part numbers, and delivery references. The generator uses a fixed random seed for reproducible output.

## Output Schema

The consolidated matrix contains the following columns:

| Column | Description |
|---|---|
| Shipper | Shipping note identifier |
| Carrier | Normalized carrier name (DHL, FedEx, UPS, Special) |
| Type | Packaging type (BULK, PALLET, BOX) |
| Mov. | SAP movement type code |
| Part Number | Component part number |
| Quantity | Units shipped |
| Delivery TX | 9-digit delivery reference (origin) |
| Delivery US | 9-digit delivery reference (destination) |
| PO | Purchase order number |
| RMA | Return material authorization |

## Tech Stack

| Tool | Role |
|---|---|
| pdfplumber | Text extraction from PDFs |
| pandas | DataFrame construction and manipulation |
| openpyxl | Excel output |
| fpdf2 | Report generation and fixture creation |

## Roadmap

- [x] **Phase 1** — Core movements (601, 643, Z61) with Excel output and synthetic fixtures
- [ ] **Phase 2** — Additional movements (122, 122K, 541, 551, 161, Z71)
- [ ] **Phase 3** — PostgreSQL output for downstream analytics
- [ ] **Phase 4** — PowerBI dashboard integration
- [ ] **Phase 5** — Integration as ingestion connector for [QuantIA](https://github.com/diegozoel/QuantIA)

## Connection to QuantIA

This ETL pipeline is the first public module of **QuantIA**, a B2B analytics platform for supply chain transparency. Shipping Doc Parser serves as the data ingestion layer — extracting and structuring raw shipping data that QuantIA then processes through quantitative models (Monte Carlo simulation, linear programming, dead stock analysis, reorder point optimization).

In Phase 3, the pipeline output transitions from Excel files to PostgreSQL, enabling direct integration with QuantIA's analytics engine.

## License

[MIT](LICENSE)
