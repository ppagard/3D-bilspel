from PyQt5.QtWidgets import QApplication
import sys
from retrofit.gui import LoanCalculatorGUI


def main():
    app = QApplication(sys.argv)
    window = LoanCalculatorGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
