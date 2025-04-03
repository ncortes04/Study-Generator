import numpy as np
import cv2
from keras.models import load_model

# Load the model
model = load_model('calendar_event_model.h5')

# Image size should match model input size
IMG_SIZE = (800, 450)

# Load the test image
image = cv2.imread('C:/Users/troyr/Desktop/Study-Generator/model/test_image.jpg')  # Update with your actual path

if image is None:
    print("Error: Image could not be loaded. Check the file path.")
else:
    # Resize image to match the model input size
    image_resized = cv2.resize(image, IMG_SIZE)

    # Preprocess image (e.g., normalize the pixel values)
    image_resized = np.array(image_resized, dtype=np.float32) / 255.0
    image_resized = np.expand_dims(image_resized, axis=0)  # Add batch dimension

    # Predict using the model
    prediction = model.predict(image_resized)

    # Print the prediction to debug
    print("Prediction:", prediction)

    # Get the bounding boxes (5 boxes with 4 values per box: cx, cy, w, h)
    bounding_boxes = prediction[0].reshape(-1, 4)
    
    print("Reshaped Bounding Boxes:", bounding_boxes)

    # Get the original image size to map bounding boxes back to the original image
    original_height, original_width = image.shape[:2]

    # Draw the predicted bounding boxes on the image
    for box in bounding_boxes:
        cx, cy, w, h = box
        # Convert from normalized (cx, cy, w, h) to pixel coordinates
        x1 = int((cx - w / 2) * original_width)
        y1 = int((cy - h / 2) * original_height)
        x2 = int((cx + w / 2) * original_width)
        y2 = int((cy + h / 2) * original_height)

        # Debug print to see the values being used for drawing the box
        print(f"Drawing box: {(x1, y1)} to {(x2, y2)}")

        # Draw a rectangle around the predicted event
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green color, thickness = 2

    # Display the image with bounding boxes
    cv2.imshow("Test Image with Bounding Boxes", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
