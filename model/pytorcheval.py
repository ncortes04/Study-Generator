import torch
from PIL import Image
import numpy as np

# Load model
model = torch.hub.load('C:/Users/troyr/Desktop/Study-Generator/yolov5', 'custom',
                       path='C:/Users/troyr/Desktop/Study-Generator/yolov5/runs/train/calendar_detector4/weights/best.pt',
                       source='local')


# Load image
img_path = 'C:/Users/troyr/Desktop/Study-Generator/test-generator/images/val/calendar_0.jpg'
img = Image.open(img_path)

# Run inference
results = model(img)

# Parse results
boxes = results.xyxy[0]  # [x1, y1, x2, y2, conf, class]
for box in boxes:
    x1, y1, x2, y2, conf, cls = box.tolist()
    print(f"Box: ({x1:.0f}, {y1:.0f}) to ({x2:.0f}, {y2:.0f}), conf: {conf:.2f}")
