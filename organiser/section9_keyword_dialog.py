import os, shutil, logging
from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout,
                             QDialogButtonBox, QMessageBox, QFileDialog, QLabel, QComboBox)
from organiser.section3_helpers import ensure_dir_exists

class KeywordOrganizerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Organise by Keyword")
        self.setGeometry(200, 200, 500, 300)
        self.init_ui()
        
    def init_ui(self):
        layout = QFormLayout()
        self.source_folder = QLineEdit()
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_folder)
        browse_source_btn = QPushButton("Browse")
        browse_source_btn.clicked.connect(self.browse_source)
        source_layout.addWidget(browse_source_btn)
        layout.addRow("Source Folder:", source_layout)
        
        self.target_folder = QLineEdit()
        target_layout = QHBoxLayout()
        target_layout.addWidget(self.target_folder)
        browse_target_btn = QPushButton("Browse")
        browse_target_btn.clicked.connect(self.browse_target)
        target_layout.addWidget(browse_target_btn)
        layout.addRow("Target Folder:", target_layout)
        
        self.keyword_input = QLineEdit()
        layout.addRow("Keywords (comma separated):", self.keyword_input)
        
        self.case_sensitive = QComboBox()
        self.case_sensitive.addItems(["Case Insensitive", "Case Sensitive"])
        layout.addRow("Case Sensitivity:", self.case_sensitive)
        
        self.result_label = QLabel("")
        layout.addRow("Results:", self.result_label)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.process_keywords)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        self.setLayout(layout)
    
    def browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_folder.setText(folder)
    
    def browse_target(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Target Folder")
        if folder:
            self.target_folder.setText(folder)
    
    def process_keywords(self):
        source = self.source_folder.text().strip()
        target = self.target_folder.text().strip()
        keywords_text = self.keyword_input.text().strip()
        case_sensitive = (self.case_sensitive.currentText() == "Case Sensitive")
        
        if not source or not target or not keywords_text:
            QMessageBox.warning(self, "Missing Information", 
                                "Please provide source folder, target folder, and keywords.")
            return
        
        keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
        
        try:
            moved_count, errors = organize_by_keyword(source, target, keywords, case_sensitive)
            if errors:
                error_msg = f"Moved {moved_count} files with {len(errors)} errors."
                QMessageBox.warning(self, "Completed with Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"Successfully moved {moved_count} files.")
            self.result_label.setText(f"Moved {moved_count} files")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred: {ex}")
            self.result_label.setText(f"Error: {ex}")

def organize_by_keyword(source_folder, target_folder, keywords, case_sensitive=False):
    ensure_dir_exists(target_folder)
    moved_count = 0
    errors = []
    
    if not case_sensitive:
        # Convert keywords to lowercase
        keywords = [kw.lower() for kw in keywords]
    
    for root, _, files in os.walk(source_folder):
        for file in files:
            file_check = file if case_sensitive else file.lower()
            if any(kw in file_check for kw in keywords):
                src_path = os.path.join(root, file)
                dest_path = os.path.join(target_folder, file)
                counter = 1
                while os.path.exists(dest_path):
                    base, ext_ = os.path.splitext(file)
                    dest_path = os.path.join(target_folder, f"{base} ({counter}){ext_}")
                    counter += 1
                try:
                    shutil.move(src_path, dest_path)
                    moved_count += 1
                    logging.info(f"Moved {src_path} -> {dest_path}")
                except Exception as ex:
                    err_msg = f"Error moving {src_path}: {ex}"
                    logging.error(err_msg)
                    errors.append(err_msg)
    return moved_count, errors