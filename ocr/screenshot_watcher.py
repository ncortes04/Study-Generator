from PIL import ImageGrab, Image
import time
import threading
import hashlib
from ocr.yolodetector import run_yolo_on_pil_image

previous_hash = None

def hash_image(image):
    small = image.resize((50, 50))
    return hashlib.md5(small.tobytes()).hexdigest()

def watch_clipboard(callback_on_results):
    global previous_hash

    def loop():
        global previous_hash
        while True:
            image = ImageGrab.grabclipboard()
            if image and isinstance(image, Image.Image):
                current_hash = hash_image(image)
                if current_hash != previous_hash:
                    previous_hash = current_hash
                    print("📋 Screenshot detected")
                    
                    # ❗ CALL THE YOLO FUNCTION HERE
                    results = run_yolo_on_pil_image(image)
                    
                    # Now results is YOLO output, not raw image
                    callback_on_results(results)
            time.sleep(0.3)

    threading.Thread(target=loop, daemon=True).start()
