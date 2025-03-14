import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QDialogButtonBox
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

def compute_directory_summary(directory):
    total_files = 0
    total_folders = 0
    total_size = 0
    if not os.path.exists(directory):
        return 0, 0, 0
    for root, dirs, files in os.walk(directory):
        total_folders += len(dirs)
        total_files += len(files)
        for file in files:
            try:
                total_size += os.path.getsize(os.path.join(root, file))
            except Exception:
                pass
    return total_files, total_folders, total_size

class SummaryDialog(QDialog):
    def __init__(self, summary_text, folder_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Organisation Summary")
        self.setGeometry(300, 300, 600, 400)
        self.folder_path = folder_path
        self.init_ui(summary_text)
    
    def init_ui(self, summary_text):
        layout = QVBoxLayout()
        self.summary_display = QTextEdit()
        self.summary_display.setReadOnly(True)
        self.summary_display.setText(summary_text)
        layout.addWidget(self.summary_display)
        self.open_folder_btn = QPushButton("Open Organised Folder")
        self.open_folder_btn.clicked.connect(self.open_folder)
        layout.addWidget(self.open_folder_btn)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
    
    def open_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.folder_path))