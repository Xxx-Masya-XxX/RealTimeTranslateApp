import sys
import time
import pygetwindow as gw
import mss
import mss.tools
import pytesseract
import cv2
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, 
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView
from deep_translator import GoogleTranslator


class WindowManager:
    @staticmethod
    def get_all_windows():
        return [w for w in gw.getWindowsWithTitle("") if w.title.strip()]

    @staticmethod
    def activate_window(title):
        window = next((w for w in gw.getWindowsWithTitle(title) if w.title == title), None)
        if window:
            window.activate()
            return True
        return False


class OCRProcessor:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    @staticmethod
    def capture_window_region(region, output_path="screenshot.png"):
        with mss.mss() as sct:
            screenshot = sct.grab(region)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)
            return output_path

    @staticmethod
    def extract_text(image_path):
        try:
            image = cv2.imread(image_path)
            image = image[30:, :]
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return pytesseract.image_to_string(gray, lang="rus+eng").strip()
        except Exception as e:
            raise RuntimeError(f"OCR Error: {e}")


class Translator:
    @staticmethod
    def translate(text, target_lang):
        try:
            return GoogleTranslator(source="auto", target=target_lang).translate(text)
        except Exception as e:
            raise RuntimeError(f"Translation Error: {e}")


class ResultTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 2)
        self.setup_table()

    def setup_table(self):
        self.setHorizontalHeaderLabels(["Оригинал", "Перевод"])
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.verticalHeader().setDefaultSectionSize(50)

    def update_content(self, original_text, translated_text):
        self.setRowCount(0)
        for orig, trans in zip(original_text.split("\n"), translated_text.split("\n")):
            row = self.insert_row(orig.strip(), trans.strip())
            self.setRowHeight(row, 50)

    def insert_row(self, original, translated):
        row = self.rowCount()
        self.insertRow(row)
        self.set_item(row, 0, original)
        self.set_item(row, 1, translated)
        return row

    def set_item(self, row, col, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setItem(row, col, item)


class ScreenshotOCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.window_manager = WindowManager()
        self.ocr_processor = OCRProcessor()
        self.translator = Translator()
        self.init_ui()
        self.load_windows()

    def init_ui(self):
        self.setWindowTitle("RTT - Real Time Translate")
        self.setGeometry(100, 100, 600, 400)
        
        self.layout = QVBoxLayout()
        self.window_combo = QComboBox()
        self.language_combo = QComboBox()
        self.screenshot_button = QPushButton("Извлечь текст")
        self.table = ResultTable()

        self.setup_comboboxes()
        self.layout.addWidget(self.window_combo)
        self.layout.addWidget(self.language_combo)
        self.layout.addWidget(self.screenshot_button)
        self.layout.addWidget(self.table)
        
        self.setLayout(self.layout)
        self.screenshot_button.clicked.connect(self.process_text)

    def setup_comboboxes(self):
        self.language_combo.addItems([
            "Русский (ru)", "Английский (en)",
            "Немецкий (de)", "Французский (fr)"
        ])

    def load_windows(self):
        self.window_combo.clear()
        for window in self.window_manager.get_all_windows():
            self.window_combo.addItem(window.title)

    def process_text(self):
        try:
            if not self.validate_selection():
                return
            
            window = self.get_selected_window()
            self.capture_and_process(window)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def validate_selection(self):
        if not self.window_combo.currentText():
            QMessageBox.warning(self, "Ошибка", "Выберите окно!")
            return False
        return True

    def get_selected_window(self):
        title = self.window_combo.currentText()
        window = next((w for w in self.window_manager.get_all_windows() if w.title == title), None)
        if not window:
            raise ValueError("Не удалось найти выбранное окно")
        return window

    def capture_and_process(self, window):
        self.window_manager.activate_window(window.title)
        time.sleep(0.5)
        
        region = {
            "left": window.left,
            "top": window.top,
            "width": window.width,
            "height": window.height
        }
        
        image_path = self.ocr_processor.capture_window_region(region)
        extracted_text = self.ocr_processor.extract_text(image_path)
        
        if not extracted_text:
            raise ValueError("Не удалось распознать текст")
        
        target_lang = self.get_target_language()
        translated_text = self.translator.translate(extracted_text, target_lang)
        
        self.table.update_content(extracted_text, translated_text)

    def get_target_language(self):
        return self.language_combo.currentText().split(" ")[-1][1:-1]


if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    app = QApplication(sys.argv)
    win = ScreenshotOCRApp()
    win.show()
    sys.exit(app.exec())