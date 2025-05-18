import sys
import os
import cv2
import pytesseract
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QTableWidget, 
    QTableWidgetItem, QLabel, QHeaderView
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from deep_translator import GoogleTranslator


class OCRTestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR Text Block Detection App")
        self.setGeometry(100, 100, 1000, 600)

        # Layout
        self.layout = QVBoxLayout()

        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Русский (ru)", "Английский (en)", "Немецкий (de)", "Французский (fr)"])

        # Buttons
        self.load_button = QPushButton("Загрузить тестовые изображения")
        self.process_button = QPushButton("Обработать изображения")

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Оригинал", "Обнаруженный текст", "Извлеченный текст", "Перевод"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Add widgets to layout
        self.layout.addWidget(self.language_combo)
        self.layout.addWidget(self.load_button)
        self.layout.addWidget(self.process_button)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        # Connect events
        self.load_button.clicked.connect(self.load_test_images)
        self.process_button.clicked.connect(self.process_images)

        # Image list
        self.test_images = []

    def load_test_images(self):
        """Load test images from test_images folder."""
        test_images_path = "test_images"
        if not os.path.exists(test_images_path):
            os.makedirs(test_images_path)

        self.test_images = [os.path.join(test_images_path, f) for f in os.listdir(test_images_path)
                             if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not self.test_images:
            self.show_message("Ошибка", "В папке test_images нет изображений!")
        else:
            self.show_message("Успешно", f"Загружено {len(self.test_images)} изображений.")

    def process_images(self):
        """Process images: detect text block, extract and translate it."""
        if not self.test_images:
            self.show_message("Ошибка", "Сначала загрузите тестовые изображения!")
            return

        self.table.setRowCount(0)

        target_lang = self.language_combo.currentText().split(" ")[-1][1:-1]

        for img_path in self.test_images:
            original_image, cropped_text_image, extracted_text = self.detect_text_block(img_path)
            translated_text = self.translate_text(extracted_text, target_lang)
            self.add_to_table(original_image, cropped_text_image, extracted_text, translated_text)

    def detect_text_block(self, image_path):
        """Detect a text block on the image, crop it and extract text."""
        image = cv2.imread(image_path)
        if image is None:
            return None, None, "Ошибка загрузки изображения"

        # Crop the top 30 pixels
        image = image[30:, :]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Use OpenCV to detect contours for text blocks
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Sort contours by area (largest likely to be text block)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        if contours:
            x, y, w, h = cv2.boundingRect(contours[0])  # Take largest contour
            cropped_image = image[y:y + h, x:x + w]
            extracted_text = pytesseract.image_to_string(cropped_image, lang="rus+eng").strip()
            return image, cropped_image, extracted_text
        else:
            return image, image, "Текст не найден"

    def translate_text(self, text, target_lang):
        """Translate the extracted text to the selected language."""
        try:
            translator = GoogleTranslator(source="auto", target=target_lang)
            return translator.translate(text)
        except Exception as e:
            return f"Ошибка перевода: {e}"

    def add_to_table(self, original_image, cropped_image, extracted_text, translated_text):
        """Add images and text results to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Convert OpenCV images to QPixmap
        def convert_cv_to_pixmap(image):
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_BGR888)
            return QPixmap.fromImage(q_image).scaled(300, 300, Qt.KeepAspectRatio)

        # Original image
        original_label = QLabel()
        original_label.setPixmap(convert_cv_to_pixmap(original_image))
        self.table.setCellWidget(row, 0, original_label)

        # Cropped text block image
        cropped_label = QLabel()
        cropped_label.setPixmap(convert_cv_to_pixmap(cropped_image))
        self.table.setCellWidget(row, 1, cropped_label)

        # Extracted text
        text_item = QTableWidgetItem(extracted_text)
        text_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.table.setItem(row, 2, text_item)

        # Translated text
        translated_item = QTableWidgetItem(translated_text)
        translated_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.table.setItem(row, 3, translated_item)

    def show_message(self, title, message):
        """Display a message box with a title and message."""
        msg = QLabel(message, self)
        msg.setAlignment(Qt.AlignCenter)
        msg.show()


if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

    app = QApplication(sys.argv)
    win = OCRTestApp()
    win.show()
    sys.exit(app.exec())
