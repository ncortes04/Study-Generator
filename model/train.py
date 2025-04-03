import tensorflow as tf
import os
import cv2
import numpy as np
from keras import layers, models
from xml.etree import ElementTree as ET
from keras import mixed_precision
from keras.backend import clear_session
from tensorflow.keras.callbacks import ReduceLROnPlateau

# Clear session to prevent memory leaks
clear_session()

# Set mixed precision for GPU
policy = mixed_precision.Policy('mixed_float16')
mixed_precision.set_global_policy(policy)

# Configure TensorFlow to use GPU memory efficiently
physical_devices = tf.config.list_physical_devices('GPU')
for device in physical_devices:
    tf.config.experimental.set_memory_growth(device, True)

# Paths to your images and labels
image_dir = "test-generator/images"
label_dir = "test-generator/labels"

# Set image size for input into the model
IMG_SIZE = (224, 224)  # Resize to 224x224 for MobileNetV2

# Total number of images you want to use for training
TOTAL_IMAGES = 500
import cv2
import numpy as np

def resize_with_padding(image, target_size=(800, 450)):
    # Get original image dimensions
    original_height, original_width = image.shape[:2]

    # Compute the scaling factor to preserve aspect ratio
    scale = min(target_size[0] / original_height, target_size[1] / original_width)

    # Resize the image according to the scale factor
    new_height = int(original_height * scale)
    new_width = int(original_width * scale)
    resized_image = cv2.resize(image, (new_width, new_height))

    # Create a new image of the target size, filled with black (padding)
    padded_image = np.zeros((target_size[0], target_size[1], 3), dtype=np.uint8)

    # Calculate the padding to be added to the image
    top = (target_size[0] - new_height) // 2
    bottom = target_size[0] - new_height - top
    left = (target_size[1] - new_width) // 2
    right = target_size[1] - new_width - left

    # Place the resized image in the center of the padded image
    padded_image[top:top+new_height, left:left+new_width] = resized_image

    return padded_image


# Prepare the dataset
def load_dataset(image_dir, label_dir, total_images=300, target_size=(800, 450)):
    image_paths = []
    bbox_labels = []

    counter = 0
    for filename in os.listdir(label_dir):
        if counter >= total_images:
            break

        label_path = os.path.join(label_dir, filename)
        image_path = os.path.join(image_dir, filename.replace('.xml', '.jpg'))  # Adjust image extension

        if os.path.exists(image_path) and os.path.exists(label_path):
            tree = ET.parse(label_path)
            root = tree.getroot()

            image = cv2.imread(image_path)
            original_height, original_width = image.shape[:2]

            # Resize with padding (preserve aspect ratio)
            image = resize_with_padding(image, target_size)

            bbox = []
            for obj in root.iter('object'):
                bndbox = obj.find('bndbox')
                if bndbox is not None:
                    xmin = int(bndbox.find('xmin').text)
                    ymin = int(bndbox.find('ymin').text)
                    xmax = int(bndbox.find('xmax').text)
                    ymax = int(bndbox.find('ymax').text)

                    # Normalize the bounding box
                    cx_resized = (xmin + xmax) / 2 / original_width
                    cy_resized = (ymin + ymax) / 2 / original_height
                    w_resized = (xmax - xmin) / original_width
                    h_resized = (ymax - ymin) / original_height

                    # Scale the bounding box to the new image size
                    cx_resized *= target_size[1]
                    cy_resized *= target_size[0]
                    w_resized *= target_size[1]
                    h_resized *= target_size[0]

                    bbox.append([cx_resized, cy_resized, w_resized, h_resized])

            # Pad the bounding boxes if necessary
            while len(bbox) < 25:
                bbox.append([0.0, 0.0, 0.0, 0.0])  # Padding for empty bounding boxes
            bbox = bbox[:25]  # Trim to 25 bounding boxes if more than 25

            bbox_labels.append(np.array(bbox).flatten())
            image_paths.append(image)

            counter += 1

    return image_paths, bbox_labels

# Normalize the images
images = np.array(images, dtype=np.float32) / 255.0
bbox_labels = np.array(bbox_labels, dtype=np.float32)

# Load the data
images, bbox_labels = load_dataset(image_dir, label_dir, total_images=TOTAL_IMAGES)

# Normalize pixel values to [0, 1]
images = np.array(images, dtype=np.float32) / 255.0

# Ensure that labels are numpy arrays and flattened to match the output shape
bbox_labels = np.array(bbox_labels, dtype=np.float32)

# Split dataset into training and validation sets (80-20 split)
train_size = int(0.8 * len(images))
X_train, X_val = images[:train_size], images[train_size:]
y_train_bbox, y_val_bbox = bbox_labels[:train_size], bbox_labels[train_size:]

# Print shapes for verification
print(f"X_train shape: {X_train.shape}, y_train_bbox shape: {y_train_bbox.shape}")
print(f"X_val shape: {X_val.shape}, y_val_bbox shape: {y_val_bbox.shape}")

# Define a simple CNN model for object detection (YOLO-like structure)
def create_advanced_model():
    # Load the MobileNetV2 model pre-trained on ImageNet without the top layer
    base_model = tf.keras.applications.MobileNetV2(input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
                             include_top=False, weights='imagenet')
    
    # Freeze the base model layers to prevent them from being trained
    base_model.trainable = False

    # Build the custom model on top of the MobileNetV2 base model
    model = tf.keras.Sequential([
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),  # Add a pooling layer to reduce the spatial dimensions
        tf.keras.layers.Dense(128, activation='relu'),
        
        # Output layer for bounding boxes (25 bounding boxes, each with 4 parameters: cx, cy, w, h)
        tf.keras.layers.Dense(25 * 4, activation='sigmoid', name="bbox_output")
    ])

    # Compile model with only the bounding box loss (MSE)
    model.compile(optimizer='adam',
                  loss={'bbox_output': 'mean_squared_error'},
                  metrics=['accuracy'])  # You can use accuracy for tracking bounding box prediction progress

    return model

# Create the model
model = create_advanced_model()

# Train model with only bounding box labels
lr_scheduler = ReduceLROnPlateau(monitor='val_loss', 
                                  factor=0.2, 
                                  patience=5, 
                                  verbose=1, 
                                  min_lr=1e-6)

model.fit(X_train, 
          {'bbox_output': y_train_bbox}, 
          validation_data=(X_val, {'bbox_output': y_val_bbox}),
          epochs=50, 
          batch_size=4,
          callbacks=[lr_scheduler])

# Save the model
model.save('calendar_event_model.h5')

print("Model training completed and saved.")
