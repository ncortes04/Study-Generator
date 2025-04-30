import pytesseract
import cv2
from PIL import Image
import time
import easyocr

reader = easyocr.Reader(['en'], gpu=True)

def extract_text_from_box(image_cv, box):
    x1, y1, x2, y2 = box

    # 🧹 Remove icon area
    x1 = min(x1 + 16, x2 - 1)

    # ✂️ Crop
    cropped = image_cv[y1:y2, x1:x2]

    # 📈 Resize small boxes (EasyOCR likes bigger inputs)
    h, w = cropped.shape[:2]
    if w < 60 or h < 20:
        cropped = cv2.resize(cropped, (w * 2, h * 2), interpolation=cv2.INTER_LINEAR)

    # 🎨 Convert to grayscale
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

    # 🌗 Adaptive thresholding (helps isolate characters)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY, blockSize=15, C=10)

    # 🧠 OCR
    results = reader.readtext(thresh, detail=0)  # no box coords, just text

    return results[0].strip() if results else "completed"