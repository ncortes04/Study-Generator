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

    # ⏱️ Preload clipboard hash to skip old image
    init_image = ImageGrab.grabclipboard()
    if init_image and isinstance(init_image, Image.Image):
        previous_hash = hash_image(init_image)

    def loop():
        global previous_hash
        while True:
            image = ImageGrab.grabclipboard()
            if image and isinstance(image, Image.Image):
                current_hash = hash_image(image)
                if current_hash != previous_hash:
                    previous_hash = current_hash
                    # print("📋 Screenshot detected")

                    # # 🧠 Run YOLO and return results
                    # results = run_yolo_on_pil_image(image)
                    callback_on_results(image)
            time.sleep(0.3)

    threading.Thread(target=loop, daemon=True).start()
