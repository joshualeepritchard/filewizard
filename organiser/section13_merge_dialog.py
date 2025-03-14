import os, shutil, logging, hashlib
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTextEdit, QDialogButtonBox, QMessageBox,
                             QFileDialog, QApplication, QProgressBar)
from organiser.section3_helpers import ensure_dir_exists

class MergeFoldersDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Merge Folders")
        self.setGeometry(300, 300, 600, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Source Folder Selection
        src_layout = QHBoxLayout()
        self.src_input = QLineEdit()
        src_browse = QPushButton("Browse")
        src_browse.clicked.connect(self.browse_src)
        src_layout.addWidget(QLabel("Source Folder:"))
        src_layout.addWidget(self.src_input)
        src_layout.addWidget(src_browse)
        layout.addLayout(src_layout)
        
        # Destination Folder Selection
        dest_layout = QHBoxLayout()
        self.dest_input = QLineEdit()
        dest_browse = QPushButton("Browse")
        dest_browse.clicked.connect(self.browse_dest)
        dest_layout.addWidget(QLabel("Destination Folder:"))
        dest_layout.addWidget(self.dest_input)
        dest_layout.addWidget(dest_browse)
        layout.addLayout(dest_layout)
        
        # Status Display
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(100)
        layout.addWidget(self.status_text)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.merge_folders)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
        self.setLayout(layout)
    
    def browse_src(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.src_input.setText(folder)
    
    def browse_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_input.setText(folder)
    
    def get_folder_hashes(self, folder):
        """
        Recursively scans the folder and returns a dictionary mapping
        file hash (SHA-256) to a list of tuples: (full_path, relative_path).
        """
        file_dict = {}
        for root, _, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'rb') as f:
                        content = f.read()
                    file_hash = hashlib.sha256(content).hexdigest()
                except Exception as e:
                    logging.error(f"Error reading file {full_path}: {e}")
                    continue
                rel_path = os.path.relpath(full_path, folder)
                if file_hash not in file_dict:
                    file_dict[file_hash] = []
                file_dict[file_hash].append((full_path, rel_path))
        return file_dict
    
    def merge_folders(self):
        source = os.path.normpath(self.src_input.text().strip())
        dest = os.path.normpath(self.dest_input.text().strip())
        
        if not source or not dest:
            QMessageBox.warning(self, "Missing Information", "Please select both source and destination folders.")
            return
        
        if not os.path.exists(source) or not os.path.exists(dest):
            QMessageBox.warning(self, "Invalid Folders", "Both folders must exist.")
            return
        
        self.status_text.append("Scanning destination folder...")
        QApplication.processEvents()
        dest_hashes = self.get_folder_hashes(dest)
        dest_hash_set = set(dest_hashes.keys())
        
        self.status_text.append("Scanning source folder...")
        QApplication.processEvents()
        source_hashes = self.get_folder_hashes(source)
        
        duplicate_count = 0
        to_move = []  # List of (src_full_path, relative_path) that are unique
        
        for file_hash, src_list in source_hashes.items():
            if file_hash in dest_hash_set:
                duplicate_count += len(src_list)
            else:
                to_move.extend(src_list)
        
        summary = (f"Found {duplicate_count} duplicate file(s) in the source folder (these will be deleted),\n"
                   f"and {len(to_move)} unique file(s) to move to the destination folder.\n\n"
                   "Do you want to proceed with the merge?")
        self.status_text.append(summary)
        QApplication.processEvents()
        
        reply = QMessageBox.question(self, "Confirm Merge", summary, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return
        
        total_operations = duplicate_count + len(to_move)
        self.progress_bar.setMaximum(total_operations)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        ops_done = 0
        
        # Delete duplicate files from source
        for file_hash, src_list in source_hashes.items():
            if file_hash in dest_hash_set:
                for src_full, rel in src_list:
                    try:
                        os.remove(src_full)
                        ops_done += 1
                        self.progress_bar.setValue(ops_done)
                        self.status_text.append(f"Deleted duplicate: {src_full}")
                        QApplication.processEvents()
                    except Exception as e:
                        logging.error(f"Error deleting file {src_full}: {e}")
        
        # Move unique files to destination
        for src_full, rel in to_move:
            dest_path = os.path.join(dest, rel)
            dest_dir = os.path.dirname(dest_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            try:
                shutil.move(src_full, dest_path)
                ops_done += 1
                self.progress_bar.setValue(ops_done)
                self.status_text.append(f"Moved: {src_full} -> {dest_path}")
                QApplication.processEvents()
            except Exception as e:
                logging.error(f"Error moving file {src_full}: {e}")
        
        self.progress_bar.setVisible(False)
        self.status_text.append("Merge completed successfully!")
        QMessageBox.information(self, "Success", "Folders merged successfully!")
        self.accept()