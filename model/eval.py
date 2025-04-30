import numpy as np
import cv2
from keras.models import load_model

# --- Config ---
MODEL_PATH = 'calendar_event_model.h5'
IMAGE_PATH = 'C:/Users/troyr/Desktop/Study-Generator/model/test_image.jpg'
IMG_SIZE = (512, 512)  # must match training input size

# --- Load model ---
model = load_model(MODEL_PATH)

# --- Load image ---
image = cv2.imread(IMAGE_PATH)
if image is None:
    print("Error: Image could not be loaded. Check the file path.")
    exit()

original_height, original_width = image.shape[:2]

# --- Resize and preprocess for prediction ---
image_resized = cv2.resize(image, IMG_SIZE)
image_resized = np.array(image_resized, dtype=np.float32) / 255.0
image_resized = np.expand_dims(image_resized, axis=0)  # Add batch dimension

# --- Predict bounding boxes ---
prediction = model.predict(image_resized)
bounding_boxes = prediction[0].reshape(-1, 4)  # (cx, cy, w, h)

print("Reshaped Bounding Boxes:", bounding_boxes)

# --- Draw boxes ---
for cx, cy, w, h in bounding_boxes:
    # Ignore zeroed-out boxes
    if w < 0.01 or h < 0.01:
        continue

    # Scale back to original image size
    x1 = int((cx - w / 2) * original_width)
    y1 = int((cy - h / 2) * original_height)
    x2 = int((cx + w / 2) * original_width)
    y2 = int((cy + h / 2) * original_height)

    print(f"Drawing box: ({x1}, {y1}) to ({x2}, {y2})")
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

# --- Show final result ---
cv2.imshow("Detected Assignments", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
