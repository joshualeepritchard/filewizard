import sys, os
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QFileDialog,
                             QComboBox, QLineEdit, QListWidget, QListWidgetItem,
                             QAbstractItemView, QVBoxLayout, QHBoxLayout, QMessageBox,
                             QProgressBar, QTextEdit, QDialog, QFormLayout, QDialogButtonBox,
                             QGridLayout, QShortcut, QRadioButton)
from PyQt5.QtGui import QKeySequence, QDesktopServices
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl

from organiser.section2_configuration import CONFIG, save_config
from organiser.section3_helpers import categorised_dir, duplicates_dir, to_be_deleted_dir
from organiser.section7_processing_thread import ProcessingThread
from organiser.section8_extension_dialog import ExtensionOrganizerDialog
from organiser.section9_keyword_dialog import KeywordOrganizerDialog
from organiser.section11_summary import SummaryDialog, compute_directory_summary
from organiser.section12_admin_dialog import FolderAdminOperationDialog
from organiser.section13_merge_dialog import MergeFoldersDialog

class OrganiseGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Wizard")
        self.setGeometry(100, 100, 900, 600)  # Increased initial width by 100px
        self.processing_thread = None
        self.init_ui()
        # Initialize folders from config
        for folder in CONFIG["target_folders"]:
            self.folder_list.addItem(folder)
        self.shortcut = QShortcut(QKeySequence("F5"), self)
        self.shortcut.activated.connect(self.refresh_ui)

    def refresh_ui(self):
        pos = self.pos()
        old_layout = self.layout()
        if old_layout:
            QWidget().setLayout(old_layout)
        self.init_ui()
        self.move(pos)

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Left panel: Configuration settings
        config_layout = QVBoxLayout()
        config_layout.setSpacing(20)

        # Target Folders Section
        folder_section = QVBoxLayout()
        folder_label = QLabel("<b>Folders to Organise:</b>")
        folder_label.setAlignment(Qt.AlignLeft)  # Align label to the left
        folder_section.addWidget(folder_label)
        #Reduced Space
        folder_section.setSpacing(10)  # Reduce spacing by half
        
        # Add/Remove Buttons
        button_layout = QHBoxLayout()
        self.add_folder_btn = QPushButton("Add Folder")
        self.remove_folder_btn = QPushButton("Remove Folder")
        self.add_folder_btn.setMinimumWidth(265)
        self.remove_folder_btn = QPushButton("Remove Folder")
        self.remove_folder_btn.setMinimumWidth(265)
        button_layout.addWidget(self.add_folder_btn)
        button_layout.addWidget(self.remove_folder_btn)
        folder_section.addLayout(button_layout)

        # Folder List
        self.folder_list = QListWidget()
        self.folder_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.folder_list.setFixedWidth(560)
        self.folder_list.setMinimumHeight(112)
        folder_section.addWidget(self.folder_list, alignment=Qt.AlignCenter)

        # Start/Stop Buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.start_btn.setMinimumWidth(265)
        self.stop_btn.setMinimumWidth(265)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        folder_section.addLayout(control_layout)
        config_layout.addLayout(folder_section)

        # Destination Section
        dest_section = QVBoxLayout()
        dest_label = QLabel("<b>File Destination Folder:</b>")
        dest_label.setAlignment(Qt.AlignLeft)  # Align label to the left
        dest_section.addWidget(dest_label)
        #Reduced Space
        dest_section.setSpacing(10)  # Reduce spacing by half
        self.root_input = QLineEdit(CONFIG.get("organised_folder", ""))
        self.root_input.setFixedWidth(560)
        dest_section.addWidget(self.root_input, alignment=Qt.AlignCenter)
        
        self.root_browse_btn = QPushButton("Browse")
        self.root_browse_btn.setMinimumWidth(150)
        self.root_browse_btn.setMaximumWidth(150)  # Ensure it doesn't exceed the width
        hbox = QHBoxLayout()
        hbox.addStretch(1)  # Push button to the right
        hbox.addWidget(self.root_browse_btn)
        dest_section.addLayout(hbox)  # Add the HBox to your Destination Section

        config_layout.addLayout(dest_section)

        # Settings Section
        settings_layout = QGridLayout()
        settings_layout.setContentsMargins(40, 10, 40, 10)
        settings_layout.setHorizontalSpacing(30)
        
        # Hash Algorithm
        self.hash_combo = QComboBox()
        self.hash_combo.addItems(["xxhash", "md5", "sha256"])
        self.hash_combo.setCurrentText(CONFIG.get("hash_algorithm", "sha256"))
        settings_layout.addWidget(QLabel("Hash Algorithm:"), 0, 0, Qt.AlignCenter)
        settings_layout.addWidget(self.hash_combo, 1, 0, Qt.AlignCenter)
        
        # File Size Limit
        self.skip_input = QLineEdit(str(CONFIG.get("skip_larger_than", 0) // (1024 * 1024)))
        settings_layout.addWidget(QLabel("Max File Size (MB):"), 0, 1, Qt.AlignCenter)
        settings_layout.addWidget(self.skip_input, 1, 1, Qt.AlignCenter)
        
        # CPU Cores
        self.cores_input = QLineEdit(str(CONFIG.get("multiprocessing_cores", 0)))
        settings_layout.addWidget(QLabel("CPU Cores (0=all):"), 0, 2, Qt.AlignCenter)
        settings_layout.addWidget(self.cores_input, 1, 2, Qt.AlignCenter)
        
        config_layout.addLayout(settings_layout)

        main_layout.addLayout(config_layout)

        # Right panel: Progress and Controls
        action_layout = QVBoxLayout()
        action_layout.setSpacing(15)

        # Progress Section
        progress_section = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("")
        progress_section.addWidget(QLabel("<b>Progress:</b>"))
        progress_section.addWidget(self.progress_bar)
        progress_section.addWidget(self.status_label)
        action_layout.addLayout(progress_section)

        # Organizer Buttons
        organizer_layout = QVBoxLayout()
        self.extension_btn = QPushButton("Organize by Extension")
        self.keyword_btn = QPushButton("Organize by Keyword")
        self.admin_btn = QPushButton("Administrative Folder Controls")
        self.merge_btn = QPushButton("Merge Folders")
        organizer_layout.addWidget(self.merge_btn)
        for btn in [self.extension_btn, self.keyword_btn, self.admin_btn]:
            btn.setMinimumWidth(150)
            organizer_layout.addWidget(btn)
        action_layout.addLayout(organizer_layout)

        # Error Display
        self.error_display = QTextEdit()
        self.error_display.setReadOnly(True)
        action_layout.addWidget(QLabel("<b>Activity Report:</b>"))
        action_layout.addWidget(self.error_display)

        # Exit Button
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setMinimumWidth(150)
        action_layout.addWidget(self.exit_btn, alignment=Qt.AlignRight)

        main_layout.addLayout(action_layout)
        self.setLayout(main_layout)

        # Connect signals
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.remove_folder_btn.clicked.connect(self.remove_folders)
        self.root_browse_btn.clicked.connect(self.browse_root)
        self.start_btn.clicked.connect(self.start_processing)
        self.stop_btn.clicked.connect(self.stop_processing)
        self.exit_btn.clicked.connect(self.close)
        self.extension_btn.clicked.connect(self.show_extension_organizer)
        self.keyword_btn.clicked.connect(self.show_keyword_organizer)
        self.admin_btn.clicked.connect(self.show_admin_controls)
        self.merge_btn.clicked.connect(self.show_merge_dialog)

    def show_merge_dialog(self):
        dialog = MergeFoldersDialog(self)
        dialog.exec_()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select a target folder")
        if folder:
            if folder not in CONFIG["target_folders"]:
                CONFIG["target_folders"].append(folder)
                self.folder_list.addItem(folder)
                save_config(CONFIG)  # Save the updated configuration

    def remove_folders(self):
        selected_items = self.folder_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select folders to remove.")
            return
        for item in selected_items:
            folder = item.text()
            CONFIG["target_folders"].remove(folder)
            self.folder_list.takeItem(self.folder_list.row(item))
        save_config(CONFIG)  # Save the updated configuration

    def browse_root(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Organised Folder")
        if folder:
            self.root_input.setText(folder)
            CONFIG["organised_folder"] = folder
            save_config(CONFIG)  # Save the updated configuration

    def compute_multiple_directories_summary(self, dirs):
        files_total = 0
        folders_total = 0
        size_total = 0
        for d in dirs:
            f_count, d_count, s_count = compute_directory_summary(d)
            files_total += f_count
            folders_total += d_count
            size_total += s_count
        return files_total, folders_total, size_total

    def start_processing(self):
        # Gather inputs and start the ProcessingThread
        target_folders = [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
        if not target_folders:
            QMessageBox.warning(self, "No Folders", "Please add at least one folder to organise.")
            return
        organised_folder = self.root_input.text().strip()
        if not organised_folder:
            QMessageBox.warning(self, "No Organised Folder", "Please specify the organised folder.")
            return
        
        # Convert skip_input from MB to bytes
        try:
            skip_size_mb = float(self.skip_input.text().strip())
        except ValueError:
            skip_size_mb = 0
        skip_size_bytes = int(skip_size_mb * 1024 * 1024)

        # Save new config values
        CONFIG["target_folders"] = target_folders
        CONFIG["organised_folder"] = organised_folder
        CONFIG["hash_algorithm"] = self.hash_combo.currentText()
        CONFIG["skip_larger_than"] = skip_size_bytes
        CONFIG["multiprocessing_cores"] = int(self.cores_input.text().strip())
        save_config(CONFIG)

        # Summarise the source before we proceed
        self.source_files, self.source_folders, self.source_size = self.compute_multiple_directories_summary(target_folders)
        size_gb = self.source_size / (1024 * 1024 * 1024)

        # Ask for confirmation
        confirm_msg = (f"Found {self.source_files} files in {self.source_folders} folders.\n"
                       f"Total size: {size_gb:.2f} GB.\n\n"
                       "Do you want to proceed?")
        reply = QMessageBox.question(self, "Confirm Organise", confirm_msg,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        # Collect all files
        all_files = []
        for folder in target_folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    full_path = os.path.join(root, file)
                    all_files.append(full_path)
        if not all_files:
            QMessageBox.information(self, "No Files", "No files found in the specified folders.")
            return

        # Prepare UI
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.status_label.setText("Starting...")
        self.error_display.clear()

        # Start thread
        self.processing_thread = ProcessingThread(
            filepaths=all_files,
            algo=CONFIG["hash_algorithm"],
            categories=CONFIG["categories"],
            skip_size=CONFIG["skip_larger_than"],
            organised_folder=organised_folder,
            target_folders=target_folders
        )
        self.processing_thread.progress_signal.connect(self.on_progress_hashing)
        self.processing_thread.progress_cat_signal.connect(self.on_progress_moving)
        self.processing_thread.done_signal.connect(self.on_done)
        self.processing_thread.error_signal.connect(self.on_error)
        self.processing_thread.start()

    def stop_processing(self):
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.status_label.setText("Stopping...")
        else:
            QMessageBox.information(self, "Not Running", "No active process to stop.")

    def on_progress_hashing(self, current, total, eta):
        if total == 0:
            pct = 100
        else:
            pct = int((current / total) * 100)
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"Hashing files... {current}/{total} ({pct}%) | ETA: {eta:.1f}s")

    def on_progress_moving(self, current, total):
        if total == 0:
            pct = 100
        else:
            pct = int((current / total) * 100)
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"Moving files... {current}/{total} ({pct}%)")

    def on_done(self, status, dup_count, nondup_count):
        if status == "success":
            self.status_label.setText("Completed successfully!")
            self.show_final_summary(dup_count, nondup_count)
        else:
            self.status_label.setText(f"Process {status}")
        self.processing_thread = None

    def on_error(self, stage, filepath, message):
        self.error_display.append(f"[{stage} ERROR] {filepath}: {message}")

    def show_extension_organizer(self):
        dialog = ExtensionOrganizerDialog(self)
        dialog.exec_()

    def show_keyword_organizer(self):
        dialog = KeywordOrganizerDialog(self)
        dialog.exec_()

    def show_admin_controls(self):
        dialog = FolderAdminOperationDialog(self)
        dialog.exec_()

    def show_final_summary(self, dup_count, nondup_count):
        cat_files, cat_folders, cat_size = compute_directory_summary(categorised_dir(CONFIG["organised_folder"]))
        dup_files, dup_folders, dup_size = compute_directory_summary(duplicates_dir(CONFIG["organised_folder"]))
        tbd_files, tbd_folders, tbd_size = compute_directory_summary(to_be_deleted_dir(CONFIG["organised_folder"]))

        # Calculate "new folder size" and reduction
        new_folder_size = cat_size  # The organised folder is the "new" folder
        if self.source_size > 0:
            size_diff = self.source_size - cat_size
            reduction_pct = ((self.source_size - cat_size) / self.source_size) * 100
        else:
            size_diff = 0
            reduction_pct = 0

        def fmt_gb(b):
            return f"{b / (1024*1024*1024):.2f} GB"

        summary_text = (
            "==== Final Summary ====\n\n"
            f"Source Folder:\n"
            f" - Total Files: {self.source_files}\n"
            f" - Total Folders: {self.source_folders}\n"
            f" - Total Size: {fmt_gb(self.source_size)}\n\n"
            f"Organised Folder:\n"
            f" - Total Files: {cat_files}\n"
            f" - Total Folders: {cat_folders}\n"
            f" - Total Size: {fmt_gb(cat_size)}\n\n"
            f"Duplicates Folder:\n"
            f" - Total Files: {dup_files}\n"
            f" - Total Folders: {dup_folders}\n"
            f" - Total Size: {fmt_gb(dup_size)}\n\n"
            f"To Be Deleted Folder:\n"
            f" - Total Files: {tbd_files}\n"
            f" - Total Folders: {tbd_folders}\n"
            f" - Total Size: {fmt_gb(tbd_size)}\n\n"
            f"Duplicates Moved: {dup_count}\n"
            f"Non-duplicates Moved: {nondup_count}\n"
            "------------------------------------\n"
            f"Reduction: {fmt_gb(self.source_size)} - {fmt_gb(cat_size)} (New Folder Size) = {fmt_gb(self.source_size - cat_size)}\n"
            f"Reduction Percentage: {reduction_pct:.2f}%\n\n"
            "Process complete."
        )

        dialog = SummaryDialog(summary_text, CONFIG["organised_folder"], parent=self)
        dialog.exec_()