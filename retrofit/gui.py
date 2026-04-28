import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTabWidget,
    QFrame,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
    QFileDialog,
    QMessageBox,
    QScrollArea,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter


def _parse_decimal(s: str) -> float:
    """
    Tolkar tal som använder decimal komma (t.ex. 5,5 eller 1 234,56).
    Accepterar både komma och punkt som decimaltecken. Vid både punkt och
    komma tolkas punkt som tusentalsavgränsare (1.234,56 -> 1234,56).
    Lancerar ValueError med ett tydligt felmeddelande om konverteringen misslyckas.
    """
    try:
        s_clean = s.strip().replace(" ", "")
        if "," in s_clean:
            if "." in s_clean:
                # Remove thousand separator
                s_clean = s_clean.replace(".", "")
            s_clean = s_clean.replace(",", ".")
        return float(s_clean)
    except Exception:
        raise ValueError(f"Ogiltigt talformat: '{s}'")


class LoanCalculatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RetroFit - Låne- och Leasingberäkning")
        self.setGeometry(100, 100, 1200, 800)

        # Load configuration from config.json
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        defaults = {
            "default_currency": "SEK",
            "decimal_places": 2,
            "use_swedish_format": True,
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = {**defaults, **json.load(f)}
            except (json.JSONDecodeError, IOError):
                self.config = defaults
        else:
            self.config = defaults

        # Initialize components
        self.database = None  # Will be initialized when needed
        self.calculator = None  # Will be imported later

        # Create the main widget and layout
        self.init_ui()

    def init_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create top section with input fields
        input_group = QGroupBox("Inmatningsfält")
        input_layout = QHBoxLayout()

        # Type selection
        type_label = QLabel("Typ:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Lån", "Leasing"])

        # Amount input
        amount_label = QLabel("Belopp (SEK):")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Ex: 100000 eller 100 000,50")

        # Interest rate input
        rate_label = QLabel("Ränta (% per år):")
        self.rate_input = QLineEdit()
        self.rate_input.setPlaceholderText("Ex: 5,5 eller 5.5")

        # Term input
        term_label = QLabel("Löptid (månader):")
        self.term_input = QLineEdit()
        self.term_input.setPlaceholderText("Ex: 60")

        # Residual value input (only for leasing)
        self.residual_label = QLabel("Residualvärde (SEK):")
        self.residual_input = QLineEdit()
        self.residual_input.setPlaceholderText("Ex: 20000 eller 20 000,50")

        # Set up the input layout
        input_layout.addWidget(type_label)
        input_layout.addWidget(self.type_combo)
        input_layout.addWidget(amount_label)
        input_layout.addWidget(self.amount_input)
        input_layout.addWidget(rate_label)
        input_layout.addWidget(self.rate_input)
        input_layout.addWidget(term_label)
        input_layout.addWidget(self.term_input)
        input_layout.addWidget(self.residual_label)
        input_layout.addWidget(self.residual_input)

        # Set up the button layout
        button_layout = QHBoxLayout()
        self.calculate_button = QPushButton("Beräkna")
        self.calculate_button.clicked.connect(self.on_calculate)

        self.save_button = QPushButton("Spara till databas")
        self.save_button.clicked.connect(self.on_save)

        self.export_button = QPushButton("Exportera till PDF")
        self.export_button.clicked.connect(self.on_export)

        # Add buttons to layout
        button_layout.addStretch()
        button_layout.addWidget(self.calculate_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.export_button)

        # Add input and button layouts to the group
        input_group.setLayout(input_layout)

        # Create result section with two columns: summary and chart
        results_layout = QHBoxLayout()

        # Left side - Summary table
        summary_group = QGroupBox("Resultat")
        self.summary_table = QTableWidget(6, 2)
        self.summary_table.setHorizontalHeaderLabels(["Fält", "Värde"])

        # Make header non-editable and set column widths
        header = self.summary_table.horizontalHeader()
        if header:
            header.setStretchLastSection(True)
        vh = self.summary_table.verticalHeader()
        if vh:
            vh.setVisible(False)

        # Set column widths
        self.summary_table.setColumnWidth(0, 150)
        self.summary_table.setColumnWidth(1, 200)

        # Set up summary layout
        summary_layout = QVBoxLayout()
        summary_layout.addWidget(self.summary_table)
        summary_group.setLayout(summary_layout)

        # Right side - Chart
        chart_group = QGroupBox("Amorteringsschema")
        self.chart_canvas = FigureCanvas(Figure(figsize=(8, 6)))

        # Set up chart layout
        chart_layout = QVBoxLayout()
        chart_layout.addWidget(self.chart_canvas)
        chart_group.setLayout(chart_layout)

        # Add summary and chart to results layout
        results_layout.addWidget(summary_group)
        results_layout.addWidget(chart_group)

        # Amorteringsschema: tabell med alla perioder
        schedule_group = QGroupBox("Amorteringsschema – alla perioder")
        schedule_scroll = QScrollArea()
        schedule_scroll.setWidgetResizable(True)
        schedule_scroll.setMaximumHeight(320)
        self.schedule_table = QTableWidget(0, 5)
        self.schedule_table.setHorizontalHeaderLabels(
            ["Månad", "Månadsb.", "Ränta", "Amortering", "Kvarvarande"]
        )
        self.schedule_table.horizontalHeader().setStretchLastSection(True)
        self.schedule_table.verticalHeader().setVisible(False)
        schedule_scroll.setWidget(self.schedule_table)
        schedule_layout = QVBoxLayout()
        schedule_layout.addWidget(schedule_scroll)
        schedule_group.setLayout(schedule_layout)

        # Tabs: Beräkna and Historik
        tab_widget = QTabWidget()
        calc_tab = QWidget()
        calc_layout = QVBoxLayout()
        calc_tab.setLayout(calc_layout)
        calc_layout.addWidget(input_group)
        calc_layout.addLayout(button_layout)
        calc_layout.addLayout(results_layout)
        calc_layout.addWidget(schedule_group)
        tab_widget.addTab(calc_tab, "Beräkna")

        # Historik tab: sparade beräkningar
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        history_tab.setLayout(history_layout)
        self.history_table = QTableWidget(0, 8)
        self.history_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Typ",
                "Belopp",
                "Ränta %",
                "Löptid",
                "Månadsb.",
                "Residual",
                "Start",
            ]
        )
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.verticalHeader().setVisible(False)
        history_btn_layout = QHBoxLayout()
        history_btn_layout.addStretch()
        btn_refresh = QPushButton("Uppdatera")
        btn_refresh.clicked.connect(self.refresh_history_table)
        btn_load = QPushButton("Ladda")
        btn_load.clicked.connect(self.on_history_load)
        btn_del = QPushButton("Radera")
        btn_del.clicked.connect(self.on_history_delete)
        history_btn_layout.addWidget(btn_refresh)
        history_btn_layout.addWidget(btn_load)
        history_btn_layout.addWidget(btn_del)
        history_layout.addWidget(self.history_table)
        history_layout.addLayout(history_btn_layout)
        tab_widget.addTab(history_tab, "Historik")

        self.tab_widget = tab_widget
        tab_widget.currentChanged.connect(self._on_tab_changed)
        self._history_data = []

        main_layout.addWidget(tab_widget)

        # Initialize the chart
        self.init_chart()

        # Connect type change signal to update UI
        self.type_combo.currentIndexChanged.connect(self.on_type_change)

        # Initially show only loan fields
        self.on_type_change(0)  # Index 0 = Lån

    def init_chart(self):
        """
        Initialize the matplotlib chart
        """
        self.figure = self.chart_canvas.figure
        self.ax = self.figure.add_subplot(111)

        # Set up the chart
        self.ax.set_title("Amorteringsschema", fontsize=14, fontweight="bold")
        self.ax.set_xlabel("Månad")
        self.ax.set_ylabel("Belopp (SEK)")

        # Set grid
        self.ax.grid(True, alpha=0.3)

        # Clear the chart
        self.ax.clear()

    def on_type_change(self, index):
        """
        Handle type change between loan and lease
        """
        if index == 0:  # Lån
            self.residual_label.hide()
            self.residual_input.hide()
        else:  # Leasing
            self.residual_label.show()
            self.residual_input.show()

    def on_calculate(self):
        """
        Handle calculate button click
        """
        # Temporarily disable the button to prevent double clicks
        self.calculate_button.setEnabled(False)
        try:
            # Get input values
            loan_type = self.type_combo.currentText()
            amount_str = self.amount_input.text().strip()
            rate_str = self.rate_input.text().strip()
            term_str = self.term_input.text().strip()
            residual_str = self.residual_input.text().strip()

            # Validate inputs
            if not amount_str or not rate_str or not term_str:
                self.show_error(
                    "Vänligen fyll i alla obligatoriska fält (belopp, ränta och löptid)"
                )
                return

            # Parse inputs (accepterar decimal komma, t.ex. 5,5 eller 1 234,56)
            amount = _parse_decimal(amount_str)
            rate = _parse_decimal(rate_str) / 100.0  # Convert percentage to decimal
            term_months = int(round(_parse_decimal(term_str)))

            if amount <= 0 or rate < 0 or term_months <= 0:
                self.show_error(
                    "Belopp och ränta måste vara positiva, löptiden måste vara större än 0"
                )
                return

            # Parse residual value if needed
            residual_value = 0.0
            if loan_type == "Leasing" and residual_str:
                try:
                    residual_value = _parse_decimal(residual_str)
                    if residual_value < 0 or residual_value >= amount:
                        self.show_error(
                            "Residualvärde måste vara positivt och mindre än beloppet"
                        )
                        return
                except ValueError:
                    self.show_error("Residualvärde måste vara ett giltigt nummer")
                    return

            # Import calculator module (lazy import to avoid circular dependencies)
            from .calculator import calculate_loan, calculate_lease

            # Calculate based on type
            if loan_type == "Lån":
                result = calculate_loan(amount, rate, term_months)
            else:  # Leasing
                result = calculate_lease(amount, rate, term_months, residual_value)

            # Store result for later use (e.g., export)
            self.current_result = result

            # Update summary table
            self.update_summary_table(result)

            # Update chart
            self.update_chart(result)

            # Update schedule table (alla perioder)
            self.update_schedule_table(result)

            # Enable save and export buttons
            self.save_button.setEnabled(True)
            self.export_button.setEnabled(True)
        except Exception as e:
            self.show_error(f"Fel vid beräkning: {str(e)}")
        finally:
            # Re‑enable the button regardless of success
            self.calculate_button.setEnabled(True)

    def update_summary_table(self, result):
        """
        Update the summary table with calculation results
        """
        # Clear existing items
        self.summary_table.clear()

        # Set up the table with headers
        self.summary_table.setHorizontalHeaderLabels(["Fält", "Värde"])

        # Define table rows
        rows = [
            ("Typ", result["type"]),
            ("Belopp", f"{result['amount']:,.2f} {self.config['default_currency']}")
            if self.config["use_swedish_format"]
            else (
                "Belopp",
                f"{result['amount']:,.2f} {self.config['default_currency']}",
            ),
            ("Ränta", f"{result['rate'] * 100:.2f}% per år"),
            ("Löptid", f"{result['term']} månader"),
            (
                "Månadsbelopp",
                f"{result['payment']:,.2f} {self.config['default_currency']}",
            )
            if self.config["use_swedish_format"]
            else (
                "Månadsbelopp",
                f"{result['payment']:,.2f} {self.config['default_currency']}",
            ),
            (
                "Totalt betalt",
                f"{result['total']:,.2f} {self.config['default_currency']}",
            )
            if self.config["use_swedish_format"]
            else (
                "Totalt betalt",
                f"{result['total']:,.2f} {self.config['default_currency']}",
            ),
        ]

        # Add rows to table
        for i, (label, value) in enumerate(rows):
            self.summary_table.setItem(i, 0, QTableWidgetItem(label))
            self.summary_table.setItem(i, 1, QTableWidgetItem(value))

        # Set row heights
        for i in range(len(rows)):
            self.summary_table.setRowHeight(i, 30)

        # Make the table read-only
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)

    def update_chart(self, result):
        """
        Update the chart with amortization schedule
        """
        # Clear previous data
        self.ax.clear()

        # Set up chart title and labels
        if result["type"] == "loan":
            self.ax.set_title("Amorteringsschema - Lån", fontsize=14, fontweight="bold")
        else:
            self.ax.set_title(
                "Amorteringsschema - Leasing", fontsize=14, fontweight="bold"
            )

        self.ax.set_xlabel("Månad")
        self.ax.set_ylabel("Belopp (SEK)")

        # Set grid
        self.ax.grid(True, alpha=0.3)

        # Extract data from schedule
        months = [item["month"] for item in result["schedule"]]
        interest_payments = [item["interest"] for item in result["schedule"]]
        principal_payments = [item["principal"] for item in result["schedule"]]

        # Create stacked bar chart
        self.ax.bar(months, interest_payments, label="Ränta", color="#ff6b6b")
        self.ax.bar(
            months,
            principal_payments,
            bottom=interest_payments,
            label="Principalkomponent",
            color="#4ecdc4",
        )

        # Add legend
        self.ax.legend()

        # Format y-axis to show SEK with commas
        self.ax.yaxis.set_major_formatter(
            FuncFormatter(lambda x, p: f"{x:,.0f} {self.config['default_currency']}")
        )

        # Adjust layout
        self.figure.tight_layout()

        # Update the canvas
        self.chart_canvas.draw()

    def update_schedule_table(self, result):
        """
        Fyller tabellen med amorteringsschema för alla perioder.
        Kolumnerna: Månad, Månadsb., Ränta, Amortering, Kvarvarande.
        """
        schedule = result.get("schedule", [])
        rem_key = (
            "remaining_principal" if result["type"] == "loan" else "remaining_balance"
        )
        self.schedule_table.setRowCount(len(schedule))
        for i, row in enumerate(schedule):
            self.schedule_table.setItem(i, 0, QTableWidgetItem(str(row["month"])))
            self.schedule_table.setItem(
                i, 1, QTableWidgetItem(self._fmt_belopp(row["payment"]))
            )
            self.schedule_table.setItem(
                i, 2, QTableWidgetItem(self._fmt_belopp(row["interest"]))
            )
            self.schedule_table.setItem(
                i, 3, QTableWidgetItem(self._fmt_belopp(row["principal"]))
            )
            self.schedule_table.setItem(
                i, 4, QTableWidgetItem(self._fmt_belopp(row[rem_key]))
            )
            self.schedule_table.setRowHeight(i, 24)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)

    def on_save(self):
        """
        Handle save button click
        """
        try:
            # Import database module (lazy import to avoid circular dependencies)
            from .database import Database

            # Initialize database connection if not already done
            if self.database is None:
                self.database = Database()

            # Save the calculation
            result_id = self.database.save_calculation(self.current_result)

            # Show success message
            QMessageBox.information(
                self, "Sparat", f"Beräkning sparad med ID: {result_id}"
            )

        except Exception as e:
            self.show_error(f"Fel vid sparande: {str(e)}")

    def on_export(self):
        """
        Handle export button click
        """
        try:
            # Import report module (lazy import to avoid circular dependencies)
            from .report import generate_pdf_report

            # Get file path for export
            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getSaveFileName(
                self,
                "Spara PDF",
                f"berakning_{self.current_result['type']}_{self.current_result['amount']:.0f}.pdf",
                "PDF Files (*.pdf);;All Files (*)",
                options=options,
            )

            if fileName:
                # Generate PDF report
                generate_pdf_report(fileName, self.current_result)

                # Show success message
                QMessageBox.information(
                    self, "Exportera", f"PDF sparad som: {fileName}"
                )

        except Exception as e:
            self.show_error(f"Fel vid export: {str(e)}")

    def _fmt_belopp(self, x):
        """Formaterar belopp med två decimaler; svenskt format (1 234,56) vid use_swedish_format."""
        s = f"{x:,.2f}"
        if self.config.get("use_swedish_format"):
            s = s.replace(",", " ").replace(".", ",")
        return s

    def _format_input_number(self, val, decimals=2):
        """Formaterar tal för inmatningsfält; använder decimal komma vid use_swedish_format."""
        if val is None:
            return ""
        v = float(val)
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        s = f"{v:.{decimals}f}".rstrip("0").rstrip(".")
        if self.config.get("use_swedish_format"):
            s = s.replace(".", ",")
        return s

    def _on_tab_changed(self, index):
        """Vid byte till fliken Historik, uppdatera listan."""
        if index == 1:
            self.refresh_history_table()

    def refresh_history_table(self):
        """Hämta sparade beräkningar från databasen och fyll tabellen."""
        try:
            from .database import Database

            if self.database is None:
                self.database = Database()
            self._history_data = self.database.get_all_calculations()
            self.history_table.setRowCount(len(self._history_data))
            for i, r in enumerate(self._history_data):
                self.history_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
                self.history_table.setItem(
                    i, 1, QTableWidgetItem("Lån" if r["type"] == "loan" else "Leasing")
                )
                self.history_table.setItem(
                    i, 2, QTableWidgetItem(f"{r['amount']:,.0f}")
                )
                self.history_table.setItem(
                    i, 3, QTableWidgetItem(f"{r['rate'] * 100:.1f}")
                )
                self.history_table.setItem(i, 4, QTableWidgetItem(str(r["term"])))
                self.history_table.setItem(
                    i, 5, QTableWidgetItem(f"{r['payment']:,.0f}")
                )
                res = r.get("residual_value")
                self.history_table.setItem(
                    i,
                    6,
                    QTableWidgetItem(
                        f"{res:,.0f}"
                        if res is not None and r["type"] == "lease"
                        else "–"
                    ),
                )
                self.history_table.setItem(i, 7, QTableWidgetItem(r["start_date"]))
        except Exception as e:
            self.show_error(f"Kunde inte hämta historik: {str(e)}")

    def on_history_load(self):
        """Ladda vald sparad beräkning in i Beräkna-fliken och beräkna om."""
        row = self.history_table.currentRow()
        if row < 0:
            self.show_error("Välj en rad att ladda.")
            return
        try:
            rec = self._history_data[row]
            self.type_combo.setCurrentIndex(0 if rec["type"] == "loan" else 1)
            self.amount_input.setText(self._format_input_number(rec["amount"]))
            self.rate_input.setText(self._format_input_number(rec["rate"] * 100, 1))
            self.term_input.setText(str(rec["term"]))
            res = rec.get("residual_value")
            self.residual_input.setText(
                self._format_input_number(res) if res is not None else ""
            )
            from .calculator import calculate_loan, calculate_lease

            if rec["type"] == "loan":
                self.current_result = calculate_loan(
                    rec["amount"], rec["rate"], rec["term"]
                )
            else:
                self.current_result = calculate_lease(
                    rec["amount"],
                    rec["rate"],
                    rec["term"],
                    res if res is not None else 0.0,
                )
            self.update_summary_table(self.current_result)
            self.update_chart(self.current_result)
            self.update_schedule_table(self.current_result)
            self.save_button.setEnabled(True)
            self.export_button.setEnabled(True)
            self.tab_widget.setCurrentIndex(0)
        except Exception as e:
            self.show_error(f"Kunde inte ladda beräkning: {str(e)}")

    def on_history_delete(self):
        """Radera vald sparad beräkning efter bekräftelse."""
        row = self.history_table.currentRow()
        if row < 0:
            self.show_error("Välj en rad att radera.")
            return
        rec = self._history_data[row]
        reply = QMessageBox.question(
            self,
            "Radera",
            f"Radera beräkning ID {rec['id']} ({rec['amount']:,.0f} {self.config['default_currency']})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            from .database import Database

            if self.database is None:
                self.database = Database()
            if self.database.delete_calculation(rec["id"]):
                self.refresh_history_table()
                QMessageBox.information(self, "Raderad", "Beräkningen är raderad.")
            else:
                self.show_error("Kunde inte radera.")
        except Exception as e:
            self.show_error(f"Kunde inte radera: {str(e)}")

    def show_error(self, message):
        """
        Show error message in a dialog
        """
        QMessageBox.critical(self, "Fel", message)

    def closeEvent(self, event):
        """
        Handle window closing
        """
        reply = QMessageBox.question(
            self,
            "Avsluta",
            "Vill du avsluta programmet?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


# Main function to run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoanCalculatorGUI()
    window.show()
    sys.exit(app.exec_())
