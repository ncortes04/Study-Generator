# ocr/screenshot_watcher.py
from PIL import ImageGrab, Image
import pytesseract
import hashlib
import time
import threading
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

previous_hash = None

def hash_image(image):
    """Create a unique hash to detect new screenshots."""
    small = image.resize((50, 50))
    return hashlib.md5(small.tobytes()).hexdigest()

def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

def watch_clipboard(callback_on_text):
    """Continuously watch the clipboard for new screenshots."""
    global previous_hash

    def loop():
        global previous_hash  # <-- Add this line
        while True:
            image = ImageGrab.grabclipboard()
            if image and isinstance(image, Image.Image):
                current_hash = hash_image(image)
                if current_hash != previous_hash:
                    previous_hash = current_hash
                    text = extract_text_from_image(image)
                    callback_on_text(text)
            time.sleep(0.3)  # Check every 300ms

    threading.Thread(target=loop, daemon=True).start()
