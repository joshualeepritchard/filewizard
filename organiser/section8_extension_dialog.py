import os, shutil, logging
from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout,
                             QDialogButtonBox, QMessageBox, QFileDialog, QLabel)
from organiser.section3_helpers import ensure_dir_exists

class ExtensionOrganizerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Organise by Extension")
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
        
        self.extension_input = QLineEdit()
        layout.addRow("Extensions (comma separated, e.g. mp3,wav):", self.extension_input)
        
        self.result_label = QLabel("")
        layout.addRow("Results:", self.result_label)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.process_extensions)
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
    
    def process_extensions(self):
        source = self.source_folder.text().strip()
        target = self.target_folder.text().strip()
        extensions_text = self.extension_input.text().strip()
        
        if not source or not target or not extensions_text:
            QMessageBox.warning(self, "Missing Information", 
                                "Please provide source folder, target folder, and extensions.")
            return
        
        extensions = [ext.strip() for ext in extensions_text.split(',')]
        
        try:
            moved_count, errors = organize_by_extension(source, target, extensions)
            if errors:
                error_msg = f"Moved {moved_count} files with {len(errors)} errors."
                QMessageBox.warning(self, "Completed with Errors", error_msg)
            else:
                QMessageBox.information(self, "Success", f"Successfully moved {moved_count} files.")
            self.result_label.setText(f"Moved {moved_count} files")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred: {ex}")
            self.result_label.setText(f"Error: {ex}")

def organize_by_extension(source_folder, target_folder, extensions):
    ensure_dir_exists(target_folder)
    moved_count = 0
    errors = []
    # Normalize extensions: ensure they start with "."
    normalized_exts = []
    for ext in extensions:
        ext = ext.strip().lower()
        if not ext.startswith('.'):
            ext = '.' + ext
        normalized_exts.append(ext)

    for root, _, files in os.walk(source_folder):
        for filename in files:
            f_lower = filename.lower()
            if any(f_lower.endswith(ext) for ext in normalized_exts):
                src_path = os.path.join(root, filename)
                dest_path = os.path.join(target_folder, filename)
                counter = 1
                while os.path.exists(dest_path):
                    base, ext_ = os.path.splitext(filename)
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