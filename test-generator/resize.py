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

# Read an image (replace the path with an actual image path)
image_path = 'path/to/your/image.jpg'
image = cv2.imread(image_path)

if image is None:
    print("Error: Image not found.")
else:
    # Call the function with your target size
    resized_image = resize_with_padding(image, target_size=(800, 450))
    
    # Show the resized image
    cv2.imshow("Resized with Padding", resized_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
