import cv2
import pytesseract
import numpy as np
import tensorflow as tf
from keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

# Load the pre-trained TensorFlow model
model = load_model('calendar_event_model.h5')

# Path to your calendar image
image_path = 'C:/Users/troyr/Desktop/Study-Generator/model/test-image.png'

# Image size should match model input size
IMG_SIZE = (400, 400)

# Load image
image = cv2.imread(image_path)

if image is None:
    print("Error: Image could not be loaded. Check the file path.")
else:
    # Resize image to match the model input size
    image_resized = cv2.resize(image, IMG_SIZE)

    # Preprocess the image for model prediction
    image_resized = np.array(image_resized, dtype=np.float32) / 255.0
    image_resized = np.expand_dims(image_resized, axis=0)  # Add batch dimension

    # Predict bounding boxes using TensorFlow model
    prediction = model.predict(image_resized)

    # Reshape prediction to detect bounding boxes (for example, 5 bounding boxes)
    num_boxes = 5
    bounding_boxes = prediction[0][:num_boxes * 4].reshape((num_boxes, 4))

    # Perform OCR using Tesseract to extract text from the image
    ocr_result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    # Iterate over OCR results and display the text and bounding boxes
    for i in range(len(ocr_result['text'])):
        if ocr_result['text'][i].strip() != "":
            # Extract the OCR bounding box coordinates
            x, y, w, h = (ocr_result['left'][i], ocr_result['top'][i], 
                          ocr_result['width'][i], ocr_result['height'][i])
            
            # Draw OCR bounding boxes on the image
            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Put the text detected in the box
            cv2.putText(image, ocr_result['text'][i], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, (255, 0, 0), 1, cv2.LINE_AA)

    # Draw TensorFlow bounding boxes on the image
    for box in bounding_boxes:
        cx, cy, w, h = box
        x1, y1, x2, y2 = int((cx - w / 2) * IMG_SIZE[0]), int((cy - h / 2) * IMG_SIZE[1]), \
                          int((cx + w / 2) * IMG_SIZE[0]), int((cy + h / 2) * IMG_SIZE[1])

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Show the final image with bounding boxes and OCR text
    cv2.imshow("Detected Events", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
