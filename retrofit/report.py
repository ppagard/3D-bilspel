from fpdf import FPDF
import datetime


class PDFReport(FPDF):
    def __init__(self, title="Rapport"):
        super().__init__()
        self.title = title

    def header(self):
        # Set font
        self.set_font("Arial", "B", 15)

        # Add title
        self.cell(0, 10, f"{self.title}", ln=True, align="C")

        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)

        # Set font
        self.set_font("Arial", "I", 8)

        # Add page number
        self.cell(0, 10, f"Sida {self.page_no()}", align="C")

    def chapter_title(self, title):
        # Set font
        self.set_font("Arial", "B", 12)

        # Background color
        self.set_fill_color(200, 220, 255)

        # Title
        self.cell(0, 10, title, ln=True, fill=True)

        # Line break
        self.ln(5)

    def chapter_body(self, body):
        # Set font
        self.set_font("Arial", "", 12)

        # Output text
        self.multi_cell(0, 10, body)

        # Line break
        self.ln()

    def add_table(self, headers, data):
        # Set font
        self.set_font("Arial", "B", 10)

        # Add headers
        for header in headers:
            self.cell(60, 10, header, border=1, align="C", fill=True)
        self.ln()

        # Set font for data
        self.set_font("Arial", "", 10)

        # Add data rows
        for row in data:
            for cell in row:
                self.cell(60, 10, str(cell), border=1, align="C")
            self.ln()

    def add_schedule_table(self, schedule, calc_type):
        """
        Lägger till amorteringsschemat som tabell med alla perioder.
        Bryter sida och upprepar rubrik vid behov.
        """
        headers = ["Månad", "Månadsb.", "Ränta", "Amortering", "Kvarvarande"]
        widths = [22, 42, 42, 42, 42]  # 190 total
        rem_key = "remaining_principal" if calc_type == "loan" else "remaining_balance"
        row_h = 7

        def _write_header():
            self.set_font("Arial", "B", 9)
            self.set_fill_color(230, 240, 255)
            for w, h in zip(widths, headers):
                self.cell(w, row_h, h, border=1, align="C", fill=True)
            self.ln()

        _write_header()
        self.set_font("Arial", "", 8)
        for row in schedule:
            if self.get_y() > 275:
                self.add_page()
                _write_header()
                self.set_font("Arial", "", 8)
            r = [
                str(row["month"]),
                f"{row['payment']:,.2f}",
                f"{row['interest']:,.2f}",
                f"{row['principal']:,.2f}",
                f"{row[rem_key]:,.2f}",
            ]
            for w, val in zip(widths, r):
                self.cell(w, row_h, val, border=1, align="R")
            self.ln()

    def add_chart(self, chart_path, width=150):
        # Add image
        self.image(chart_path, x=40, y=None, w=width)

        # Line break
        self.ln(10)


def generate_pdf_report(filename: str, calculation_data: dict):
    """
    Generate a PDF report with the calculation results

    Args:
        filename: Path to save the PDF file
        calculation_data: Dictionary containing the calculation results
    """
    # Create PDF object
    pdf = PDFReport(title=f"Rapport - {calculation_data['type'].title()} Beräkning")

    # Add a page
    pdf.add_page()

    # Set auto page break
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add title
    pdf.chapter_title("Beräkningsrapport")

    # Add date
    now = datetime.datetime.now()
    pdf.chapter_body(f"Datum: {now.strftime('%Y-%m-%d %H:%M')}\n")

    # Add calculation details
    pdf.chapter_title("Beräkningsdata")

    # Create data for the table
    headers = ["Fält", "Värde"]
    data = [
        ["Typ", calculation_data["type"].title()],
        ["Belopp", f"{calculation_data['amount']:,.2f} SEK"],
        ["Ränta", f"{calculation_data['rate'] * 100:.2f}% per år"],
        ["Löptid", f"{calculation_data['term']} månader"],
        ["Månadsbelopp", f"{calculation_data['payment']:,.2f} SEK"],
        ["Totalt betalt", f"{calculation_data['total']:,.2f} SEK"],
    ]
    if calculation_data["type"] == "lease":
        data.insert(4, ["Residualvärde", f"{calculation_data['residual_value']:,.2f} SEK"])

    # Add table
    pdf.add_table(headers, data)

    # Add amortization schedule chart
    pdf.chapter_title("Amorteringsschema")

    # Create a temporary chart file
    import matplotlib.pyplot as plt
    from io import BytesIO

    # Create the chart
    fig, ax = plt.subplots(figsize=(8, 6))

    # Set up chart
    if calculation_data["type"] == "loan":
        ax.set_title("Amorteringsschema - Lån", fontsize=14, fontweight="bold")
    else:
        ax.set_title("Amorteringsschema - Leasing", fontsize=14, fontweight="bold")

    ax.set_xlabel("Månad")
    ax.set_ylabel("Belopp (SEK)")

    # Set grid
    ax.grid(True, alpha=0.3)

    # Extract data from schedule
    months = [item["month"] for item in calculation_data["schedule"]]
    interest_payments = [item["interest"] for item in calculation_data["schedule"]]
    principal_payments = [item["principal"] for item in calculation_data["schedule"]]

    # Create stacked bar chart
    ax.bar(months, interest_payments, label="Ränta", color="#ff6b6b")
    ax.bar(
        months,
        principal_payments,
        bottom=interest_payments,
        label="Principalkomponent",
        color="#4ecdc4",
    )

    # Add legend
    ax.legend()

    # Format y-axis to show SEK with commas
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:,.0f} SEK"))

    # Adjust layout
    fig.tight_layout()

    # Save chart to BytesIO object
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    buffer.seek(0)

    # Close the figure to free memory
    plt.close(fig)

    # Add chart to PDF (save buffer as temporary file)
    temp_chart_path = "temp_chart.png"
    with open(temp_chart_path, "wb") as f:
        f.write(buffer.read())

    # Add chart to PDF
    pdf.add_chart(temp_chart_path, width=150)

    # Clean up temporary file
    import os

    if os.path.exists(temp_chart_path):
        os.remove(temp_chart_path)

    # Amorteringsschema - tabell med alla perioder
    pdf.chapter_title("Amorteringsschema - alla perioder")
    pdf.add_schedule_table(calculation_data["schedule"], calculation_data["type"])

    # Save the PDF
    pdf.output(filename)

    print(f"PDF report generated successfully: {filename}")
