import os, shutil, logging, subprocess
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QRadioButton, QWidget, QDialogButtonBox,
                             QMessageBox, QFileDialog, QApplication, QProgressBar)

from organiser.section3_helpers import ensure_dir_exists

class FolderAdminOperationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Folder Administrative Operations")
        self.setGeometry(300, 300, 600, 300)  # Increased height to accommodate progress bar
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Row: Select folder to operate on
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        folder_browse_btn = QPushButton("Browse")
        folder_browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(QLabel("Folder:"))
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(folder_browse_btn)
        layout.addLayout(folder_layout)
        
        # Row: Choose operation via radio buttons
        operation_layout = QHBoxLayout()
        self.move_radio = QRadioButton("Move Folder")
        self.delete_radio = QRadioButton("Delete Folder")
        self.delete_radio.setChecked(True)
        operation_layout.addWidget(self.move_radio)
        operation_layout.addWidget(self.delete_radio)
        layout.addLayout(operation_layout)
        
        # Row: Destination (only visible if Move is selected)
        self.dest_widget = QWidget()
        self.dest_layout = QHBoxLayout(self.dest_widget)
        self.dest_input = QLineEdit()
        dest_browse_btn = QPushButton("Browse Destination")
        dest_browse_btn.clicked.connect(self.browse_destination)
        self.dest_layout.addWidget(QLabel("Destination:"))
        self.dest_layout.addWidget(self.dest_input)
        self.dest_layout.addWidget(dest_browse_btn)
        layout.addWidget(self.dest_widget)
        self.dest_widget.setVisible(False)
        self.move_radio.toggled.connect(self.toggle_destination)
        
        # Row: Progress Bar (for deletion progress)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Row: Action buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.execute_operation)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
        self.setLayout(layout)
    
    def toggle_destination(self):
        self.dest_widget.setVisible(self.move_radio.isChecked())
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_input.setText(folder)
    
    def browse_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_input.setText(folder)
    
    def execute_operation(self):
        folder = os.path.normpath(self.folder_input.text().strip())
        if not folder:
            QMessageBox.warning(self, "No Folder", "Please select a folder to operate on.")
            return
        
        if self.move_radio.isChecked():
            dest = os.path.normpath(self.dest_input.text().strip())
            if not dest:
                QMessageBox.warning(self, "No Destination", "Please select a destination folder.")
                return
            success, msg = self.force_move_folder(folder, dest)
        else:
            # For deletion, use the progress-enabled deletion routine.
            success, msg = self.delete_folder_with_progress(folder)
            
        if success:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def delete_folder_with_progress(self, folder):
        # Enumerate all files and directories in the folder (bottom-up)
        all_files = []
        all_dirs = []
        for root, dirs, files in os.walk(folder, topdown=False):
            for f in files:
                all_files.append(os.path.join(root, f))
            for d in dirs:
                all_dirs.append(os.path.join(root, d))
        total_files = len(all_files)
        if total_files == 0:
            total_files = 1  # avoid division by zero
        
        self.progress_bar.setMaximum(total_files)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        count = 0
        # Delete each file individually
        for file in all_files:
            norm_file = os.path.normpath(file)
            # Build command for each file: take ownership, grant permissions, and delete.
            command = f'takeown /f "{norm_file}" /d y && icacls "{norm_file}" /grant Everyone:F /T && del /f /q "{norm_file}"'
            proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            count += 1
            self.progress_bar.setValue(count)
            QApplication.processEvents()  # update the UI
        
        # Delete directories (bottom-up)
        for d in all_dirs:
            try:
                os.rmdir(d)
            except Exception as e:
                logging.error(f"Error deleting directory {d}: {e}")
        # Finally, delete the top folder
        try:
            os.rmdir(folder)
        except Exception as e:
            logging.error(f"Error deleting folder {folder}: {e}")
        
        self.progress_bar.setVisible(False)
        
        if os.path.exists(folder):
            return (False, "Error: Folder still exists. Please run the program as administrator and ensure no process is using the folder.")
        return (True, "Folder deleted successfully.")
    
    def force_move_folder(self, folder, destination):
        try:
            folder = os.path.normpath(folder)
            destination = os.path.normpath(destination)
            ensure_dir_exists(destination)
            dest_path = os.path.join(destination, os.path.basename(folder))
            command = (
                f'takeown /f "{folder}" /r /d y && '
                f'icacls "{folder}" /grant Everyone:F /T && '
                f'robocopy "{folder}" "{dest_path}" /MIR && '
                f'rd /s /q "{folder}"'
            )
            proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode != 0:
                err_msg = proc.stderr.decode().strip() or "Unknown error"
                if os.path.exists(folder):
                    return (False, f"Error moving folder: {err_msg}\nPlease run the program as administrator.")
            return (True, "Folder moved successfully.")
        except Exception as e:
            return (False, f"Exception occurred: {e}")