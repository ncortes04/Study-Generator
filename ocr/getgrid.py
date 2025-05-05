from ocr.exctract import extract_text_from_box
import numpy as np
import cv2

def group_boxes_by_grid(boxes, x_tolerance=100, y_tolerance=100):
    """
    Groups boxes into grid cells by proximity in x and y, preferring row-first (top-down).
    This ensures calendar is processed in rows (left to right, top to bottom).
    """
    grid = []

    # ⬆️⬇️ Sort by y first (top to bottom), then x (left to right)
    for box in sorted(boxes, key=lambda b: (b[1], b[0])):
        x1, y1 = box[0], box[1]
        matched = False

        for group in grid:
            gx, gy = group[0][0], group[0][1]
            if abs(gy - y1) <= y_tolerance and abs(gx - x1) <= x_tolerance:
                group.append(box)
                matched = True
                break

        if not matched:
            grid.append([box])

    print(f"✅ Grouped {len(boxes)} boxes into {len(grid)} total event groups")
    return grid




def organize_calendar_entries(groups, image_cv, classes):
    results_by_day = []

    for group in groups:  # Already sorted top-down
        day_entries = []
        for box in sorted(group, key=lambda b: b[0]):  # Sort left to right
            x1, y1, x2, y2, cls, *_ = box
            class_label = classes[cls] if cls < len(classes) else "Unknown"
            extracted_text = extract_text_from_box(image_cv, (x1, y1, x2, y2))
            day_entries.append((class_label, extracted_text))
        results_by_day.append(day_entries)

    return results_by_day

def draw_grouped_boxes(image_cv, grouped_boxes, label_prefix="Group"):
    """
    Draws each group in a different color on the image for visual debugging.
    """
    for i, group in enumerate(grouped_boxes):
        # Pick a random color for each group
        color = tuple(int(x) for x in np.random.randint(100, 255, size=3))

        for box in group:
            x1, y1, x2, y2 = map(int, box[:4])
            label = f"{label_prefix} {i+1}"
            cv2.rectangle(image_cv, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                image_cv, label, (x1, y1 - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA
            )
