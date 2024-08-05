import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget,
                               QProgressBar, QTextEdit, QLabel, QFileDialog,
                               QHBoxLayout)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont, QIcon
import subprocess

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
        self.setWindowTitle("Folder Content Printer")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
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
            QTextEdit {
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
        """)

        main_layout = QVBoxLayout()

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

        main_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        main_layout.addWidget(self.text_area)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.output_folder = None

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())