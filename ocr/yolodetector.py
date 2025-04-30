import torch
import torchvision.transforms as transforms
from PIL import ImageEnhance, ImageFilter
import pathlib

# Patch pathlib
temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

# Load model ONCE
model = torch.hub.load(
    'C:/Users/troyr/Desktop/Study-Generator/yolov5',
    'custom',
    path='C:/Users/troyr/Desktop/Study-Generator/yolov5/runs/train/calendar_detector_class4_200ValFinal/weights/best.pt',
    source='local',
    force_reload=False
)
model.conf = 0.25


def run_yolo_on_pil_image(pil_image):
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    try:
        results = model(pil_image)
        return results
    except Exception as e:
        print("❌ Exception running YOLO:", e)
        return pil_image  

def remove_duplicate_boxes(boxes, iou_thresh=0.2, overlap_thresh=0.2):
    deduped = []
    used = set()

    def compute_iou(box1, box2):
        x1, y1, x2, y2 = box1[:4]
        x1b, y1b, x2b, y2b = box2[:4]

        inter_left = max(x1, x1b)
        inter_top = max(y1, y1b)
        inter_right = min(x2, x2b)
        inter_bottom = min(y2, y2b)

        if inter_right < inter_left or inter_bottom < inter_top:
            return 0.0, 0.0, 0.0  # No intersection

        inter_area = (inter_right - inter_left) * (inter_bottom - inter_top)
        area1 = (x2 - x1) * (y2 - y1)
        area2 = (x2b - x1b) * (y2b - y1b)

        iou = inter_area / float(area1 + area2 - inter_area)
        overlap1 = inter_area / area1
        overlap2 = inter_area / area2
        return iou, overlap1, overlap2

    for i, box in enumerate(boxes):
        if i in used:
            continue
        for j, other in enumerate(boxes):
            if i == j or j in used:
                continue
            iou, overlap1, overlap2 = compute_iou(box, other)
            if iou > iou_thresh or overlap1 > overlap_thresh or overlap2 > overlap_thresh:
                # ❗ Remove the box that is more "inside"
                if overlap1 > overlap2:
                    used.add(i)
                else:
                    used.add(j)
        if i not in used:
            deduped.append(box)

    return deduped
