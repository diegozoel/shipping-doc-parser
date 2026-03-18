from fpdf import FPDF


class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Extraction Process Report - Shipping Doc Parser", border=False, ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def generate_report(success_list, error_list, output_path):
    # Sort by Movement (Primary) and File Name (Secondary)
    success_list = sorted(success_list, key=lambda x: (x['move'], x['file'].lower()))
    error_list = sorted(error_list, key=lambda x: x['file'].lower())

    pdf = PDFReport()
    pdf.add_page()

    # --- SUCCESS SECTION ---
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 10, "Successfully Processed Files", ln=True)

    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(0)
    pdf.cell(70, 7, "File Name", border=1)
    pdf.cell(25, 7, "Movement", border=1)
    pdf.cell(25, 7, "Layout", border=1)
    pdf.cell(30, 7, "Carrier", border=1)
    pdf.cell(15, 7, "Items", border=1, ln=True, align="C")

    pdf.set_font("Arial", "", 8)
    for item in success_list:
        pdf.cell(70, 6, item['file'][:40], border=1)
        pdf.cell(25, 6, item['move'], border=1)
        pdf.cell(25, 6, item['layout'], border=1)
        pdf.cell(30, 6, item['carrier'], border=1)
        pdf.cell(15, 6, str(item['items']), border=1, ln=True, align="C")

    pdf.ln(10)

    # --- ERROR SECTION ---
    if error_list:
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(150, 0, 0)
        pdf.cell(0, 10, "Failed Files / Errors", ln=True)

        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(0)
        pdf.cell(80, 7, "File Name", border=1)
        pdf.cell(100, 7, "Error Message", border=1, ln=True)

        pdf.set_font("Arial", "", 8)
        for err in error_list:
            pdf.cell(80, 6, err['file'][:45], border=1)
            pdf.cell(100, 6, str(err['error'])[:60], border=1, ln=True)

    pdf.output(str(output_path))
