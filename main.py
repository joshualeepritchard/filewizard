import sys
from PyQt5.QtWidgets import QApplication
from organiser.section10_gui import OrganiseGUI

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    dark_style = """
    QWidget {
        background-color: #121212;
        color: #e0e0e0;
        font-family: "Segoe UI", sans-serif;
        font-size: 10pt;
    }
    QPushButton {
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
            stop:0 #6A1B9A, stop:1 #C2185B);
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 6px;
    }
    QPushButton:hover {
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
            stop:0 #5e1788, stop:1 #b81550);
    }
    QLineEdit, QListWidget, QProgressBar, QTextEdit {
        background-color: #1e1e1e;
        color: #e0e0e0;
        border: 1px solid #444444;
        border-radius: 4px;
        padding: 4px;
    }
    QProgressBar {
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #6A1B9A;
    }
    """
    app.setStyleSheet(dark_style)
    gui = OrganiseGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()