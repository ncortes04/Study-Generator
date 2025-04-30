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

# Model (and input) image size
IMG_SIZE = (224, 224)  # We will train on 224x224 images

# Total number of images you want to use for training
TOTAL_IMAGES = 500

def resize_with_padding(image, target_size=(512, 512)):
    """
    Resize an image to exactly the target_size while preserving its aspect ratio.
    This function returns a new image of size target_size that contains the resized image 
    centered, with black padding filling the remainder.
    """
    original_height, original_width = image.shape[:2]
    scale = min(target_size[0] / original_height, target_size[1] / original_width)
    new_height = int(original_height * scale)
    new_width = int(original_width * scale)
    
    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))
    
    # Create a padded image of the target dimensions (filled with black)
    padded_image = np.zeros((target_size[0], target_size[1], 3), dtype=np.uint8)
    
    # Calculate the offsets (padding on top and left)
    top_offset = (target_size[0] - new_height) // 2
    left_offset = (target_size[1] - new_width) // 2
    
    # Place the resized image in the center of the padded image
    padded_image[top_offset:top_offset+new_height, left_offset:left_offset+new_width] = resized_image
    return padded_image, scale, top_offset, left_offset

def load_dataset(image_dir, label_dir, total_images=300, target_size=IMG_SIZE):
    """
    Load images and their corresponding bounding box labels (from XML).
    The images are resized to target_size with padding, and the bounding box 
    coordinates are transformed using the same scale and offset so that they match the new image.
    """
    images_list = []
    bbox_labels_list = []
    counter = 0

    for filename in os.listdir(label_dir):
        if counter >= total_images:
            break

        label_path = os.path.join(label_dir, filename)
        image_path = os.path.join(image_dir, filename.replace('.xml', '.jpg'))  # Adjust image extension if needed

        if os.path.exists(image_path) and os.path.exists(label_path):
            # Parse XML for boxes
            tree = ET.parse(label_path)
            root = tree.getroot()

            # Read the original image
            image = cv2.imread(image_path)
            if image is None:
                continue  # skip if image couldn't be loaded

            original_height, original_width = image.shape[:2]

            # Resize image and get the scale and offsets
            resized_image, scale, top_offset, left_offset = resize_with_padding(image, target_size)

            bbox = []
            for obj in root.iter('object'):
                bndbox = obj.find('bndbox')
                if bndbox is not None:
                    # Get original bounding box coordinates
                    xmin = int(bndbox.find('xmin').text)
                    ymin = int(bndbox.find('ymin').text)
                    xmax = int(bndbox.find('xmax').text)
                    ymax = int(bndbox.find('ymax').text)

                    # Transform the coordinates using the scale and offsets
                    new_xmin = xmin * scale + left_offset
                    new_ymin = ymin * scale + top_offset
                    new_xmax = xmax * scale + left_offset
                    new_ymax = ymax * scale + top_offset

                    # Compute center, width, and height in the resized image space
                    cx = (new_xmin + new_xmax) / 2
                    cy = (new_ymin + new_ymax) / 2
                    w_box = new_xmax - new_xmin
                    h_box = new_ymax - new_ymin
                    bbox.append([cx, cy, w_box, h_box])
            
            # Pad the list of bounding boxes up to 25 entries (for fixed output dimensions)
            while len(bbox) < 25:
                bbox.append([0.0, 0.0, 0.0, 0.0])
            bbox = bbox[:25]  # Trim if more than 25

            images_list.append(resized_image)
            bbox_labels_list.append(np.array(bbox).flatten())
            counter += 1

    return images_list, bbox_labels_list

# Load the data using the new load_dataset function.
images, bbox_labels = load_dataset(image_dir, label_dir, total_images=TOTAL_IMAGES, target_size=IMG_SIZE)

# Normalize pixel values to [0, 1] for training
images = np.array(images, dtype=np.float32) / 255.0
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
    # Load MobileNetV2 model pre-trained on ImageNet without the top layer
    base_model = tf.keras.applications.MobileNetV2(
    input_shape=(None, None, 3),  # makes it flexible
    include_top=False,
    weights='imagenet'
)

    base_model.trainable = False  # Freeze base model layers

    model = tf.keras.Sequential([
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),  # Reduce spatial dimensions
        tf.keras.layers.Dense(128, activation='relu'),
        # Output layer: 25 boxes * 4 parameters (center_x, center_y, width, height)
        tf.keras.layers.Dense(25 * 4, activation='sigmoid', name="bbox_output")
    ])

    model.compile(optimizer='adam',
                  loss={'bbox_output': 'mean_squared_error'},
                  metrics=['accuracy'])
    return model

# Create the model
model = create_advanced_model()

# Define learning rate scheduler
lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, verbose=1, min_lr=1e-6)

# Train model with bounding box labels
model.fit(X_train,
          {'bbox_output': y_train_bbox},
          validation_data=(X_val, {'bbox_output': y_val_bbox}),
          epochs=50,
          batch_size=4,
          callbacks=[lr_scheduler])

# Save the model
model.save('calendar_event_model.h5')
print("Model training completed and saved.")
