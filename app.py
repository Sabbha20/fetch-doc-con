import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget,
                               QProgressBar, QTextEdit, QLabel, QFileDialog)
from PySide6.QtCore import QThread, Signal


class WorkerThread(QThread):
    progress_update = Signal(int)
    status_update = Signal(str)
    processing_complete = Signal(str)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        output_file = 'output.txt'
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
                self.status_update.emit(f"Fetching info for: {file_path}")

                f.write(f"File: {file_path}\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as file_content:
                        content = file_content.read()
                        f.write(f"Content:\n{content}\n")
                except Exception as e:
                    f.write(f"Error reading file: {e}\n")
                f.write("\n" + "=" * 50 + "\n\n")

        self.progress_update.emit(100)
        self.status_update.emit("Completed")
        self.processing_complete.emit(
            f"Contents have been written to {output_file}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folder Content Printer")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.select_button = QPushButton("Select Folder")
        self.select_button.clicked.connect(self.select_folder)
        layout.addWidget(self.select_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.text_area.clear()
            self.progress_bar.setValue(0)
            self.status_label.setText("")

            self.worker = WorkerThread(folder_path)
            self.worker.progress_update.connect(self.update_progress)
            self.worker.status_update.connect(self.update_status)
            self.worker.processing_complete.connect(self.processing_done)
            self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.text_area.append(message)

    def processing_done(self, message):
        self.status_label.setText(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())