import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget, QProgressBar, QTextEdit,
                               QLabel, QFileDialog, QHBoxLayout, QLineEdit,
                               QMessageBox, QTabWidget)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont, QIcon
import subprocess
import pikepdf
from docx import Document
import openpyxl
import xml.etree.ElementTree as ET

class DocumentUnlocker:
    @staticmethod
    def unlock_pdf(file_path, password):
        try:
            with pikepdf.open(file_path, password=password) as pdf:
                unlocked_path = file_path.replace('.pdf', '_unlocked.pdf')
                pdf.save(unlocked_path)
            return unlocked_path
        except Exception as e:
            raise Exception(f"Failed to unlock PDF: {str(e)}")

    @staticmethod
    def unlock_docx(file_path, password):
        try:
            doc = Document(file_path, password=password)
            unlocked_path = file_path.replace('.docx', '_unlocked.docx')
            doc.save(unlocked_path)
            return unlocked_path
        except Exception as e:
            raise Exception(f"Failed to unlock DOCX: {str(e)}")

    @staticmethod
    def unlock_xlsx(file_path, password):
        try:
            workbook = openpyxl.load_workbook(file_path, password=password)
            unlocked_path = file_path.replace('.xlsx', '_unlocked.xlsx')
            workbook.save(unlocked_path)
            return unlocked_path
        except Exception as e:
            raise Exception(f"Failed to unlock XLSX: {str(e)}")

    @staticmethod
    def unlock_xml(file_path, password):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # Implement XML unlocking logic here if needed
            unlocked_path = file_path.replace('.xml', '_unlocked.xml')
            tree.write(unlocked_path)
            return unlocked_path
        except Exception as e:
            raise Exception(f"Failed to unlock XML: {str(e)}")

class WorkerThread(QThread):
    progress_update = Signal(int)
    status_update = Signal(str)
    processing_complete = Signal(str)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        output_file = os.path.join(self.folder_path, 'output.txt')
        file_paths = []

        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                file_paths.append(os.path.join(root, file))

        total_files = len(file_paths)
        if total_files == 0:
            self.status_update.emit("No files found in the selected folder.")
            return

        with open(output_file, 'w', encoding='utf-8') as f:
            for i, file_path in enumerate(file_paths):
                progress = int((i / total_files) * 100)
                self.progress_update.emit(progress)
                self.status_update.emit(f"Processing: {file_path}")

                f.write(f"File: {file_path}\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as file_content:
                        content = file_content.read()
                        f.write(f"Content:\n{content}\n")
                except Exception as e:
                    f.write(f"Error reading file: {e}\n")
                f.write("\n" + "=" * 50 + "\n\n")

        self.progress_update.emit(100)
        self.status_update.emit("Processing completed")
        self.processing_complete.emit(output_file)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elegant Document Processor")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow, QTabWidget::pane {
                background-color: #2E2E2E;
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #4A4A4A;
                color: #E0E0E0;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                border: 1px solid #5A5A5A;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
            QPushButton:pressed {
                background-color: #3A3A3A;
            }
            QProgressBar {
                border: 2px solid #5A5A5A;
                border-radius: 5px;
                text-align: center;
                color: #E0E0E0;
                background-color: #2E2E2E;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 3px;
            }
            QTextEdit, QLineEdit {
                background-color: #3E3E3E;
                color: #E0E0E0;
                border: 2px solid #5A5A5A;
                border-radius: 5px;
                padding: 5px;
                font-family: Consolas, Monaco, monospace;
            }
            QLabel {
                color: #E0E0E0;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #4A4A4A;
                color: #E0E0E0;
                padding: 8px 16px;
                margin: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #5A5A5A;
            }
        """)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.folder_tab = QWidget()
        self.unlock_tab = QWidget()

        self.tab_widget.addTab(self.folder_tab, "Folder Processing")
        self.tab_widget.addTab(self.unlock_tab, "Unlock Document")

        self.setup_folder_tab()
        self.setup_unlock_tab()

    def setup_folder_tab(self):
        layout = QVBoxLayout()

        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select Folder")
        self.select_button.clicked.connect(self.select_folder)
        button_layout.addWidget(self.select_button)

        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_button)

        self.open_folder_button = QPushButton("Open Output Folder")
        self.open_folder_button.clicked.connect(self.open_output_folder)
        self.open_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_folder_button)

        layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.folder_tab.setLayout(layout)

    def setup_unlock_tab(self):
        layout = QVBoxLayout()

        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select a file to unlock")
        file_layout.addWidget(self.file_path_input)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_button)

        layout.addLayout(file_layout)

        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)

        layout.addLayout(password_layout)

        self.unlock_button = QPushButton("Unlock Document")
        self.unlock_button.clicked.connect(self.unlock_document)
        layout.addWidget(self.unlock_button)

        self.unlock_status = QLabel()
        self.unlock_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.unlock_status)

        layout.addStretch()

        self.unlock_tab.setLayout(layout)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.text_area.clear()
            self.progress_bar.setValue(0)
            self.status_label.setText("")
            self.output_folder = folder_path

            self.worker = WorkerThread(folder_path)
            self.worker.progress_update.connect(self.update_progress)
            self.worker.status_update.connect(self.update_status)
            self.worker.processing_complete.connect(self.processing_done)
            self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.text_area.append(message)

    def processing_done(self, output_file):
        self.status_label.setText(f"Output saved to: {output_file}")
        self.open_folder_button.setEnabled(True)

    def clear_log(self):
        self.text_area.clear()

    def open_output_folder(self):
        if self.output_folder:
            if sys.platform == "win32":
                os.startfile(self.output_folder)
            elif sys.platform == "darwin":  # macOS
                subprocess.Popen(["open", self.output_folder])
            else:  # Linux and other Unix-like
                subprocess.Popen(["xdg-open", self.output_folder])

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.file_path_input.setText(file_path)

    def unlock_document(self):
        file_path = self.file_path_input.text()
        password = self.password_input.text()

        if not file_path or not password:
            self.unlock_status.setText("Please select a file and enter a password.")
            return

        try:
            _, extension = os.path.splitext(file_path)
            extension = extension.lower()

            if extension == '.pdf':
                unlocked_path = DocumentUnlocker.unlock_pdf(file_path, password)
            elif extension == '.docx':
                unlocked_path = DocumentUnlocker.unlock_docx(file_path, password)
            elif extension == '.xlsx':
                unlocked_path = DocumentUnlocker.unlock_xlsx(file_path, password)
            elif extension == '.xml':
                unlocked_path = DocumentUnlocker.unlock_xml(file_path, password)
            else:
                self.unlock_status.setText(f"Unsupported file type: {extension}")
                return

            self.unlock_status.setText(f"Document unlocked successfully. Saved as: {unlocked_path}")
        except Exception as e:
            self.unlock_status.setText(f"Error unlocking document: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())