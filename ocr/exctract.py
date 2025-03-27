# ocr/extract.py
import pytesseract

def extract_text(image):
    return pytesseract.image_to_string(image)
