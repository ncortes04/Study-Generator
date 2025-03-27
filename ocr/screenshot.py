# ocr/screenshot.py
from PIL import ImageGrab, Image
import hashlib

def get_screenshot():
    image = ImageGrab.grabclipboard()
    return image if isinstance(image, Image.Image) else None

def hash_image(image):
    small = image.resize((50, 50))
    return hashlib.md5(small.tobytes()).hexdigest()
