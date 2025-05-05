from ocr.screenshot_watcher import watch_clipboard
from ocr.yolodetector import run_yolo_on_pil_image, remove_duplicate_boxes
from ui.window import create_ui
from Appstate import AppState
from PIL import Image, ImageGrab
import numpy as np
import cv2


def split_into_tiles(image, tile_size=(512, 512), tile_threshold=700):
    tiles = []
    img_w, img_h = image.size
    tile_w, tile_h = tile_size

    if img_w <= tile_threshold and img_h <= tile_threshold:
        tiles.append((image, (0, 0)))
        return tiles

    for top in range(0, img_h, tile_h):
        for left in range(0, img_w, tile_w):
            right = min(left + tile_w, img_w)
            bottom = min(top + tile_h, img_h)
            tile = image.crop((left, top, right, bottom))
            if right - left >= 200:
                tiles.append((tile, (left, top)))
    return tiles

def crosses_tile_edge(x1, x2, tile_size=512, edge_thresh=20, test_mode = False):
    near_left_edge = (x1 % tile_size < edge_thresh) or ((tile_size - (x1 % tile_size)) < edge_thresh)
    near_right_edge = (x2 % tile_size < edge_thresh) or ((tile_size - (x2 % tile_size)) < edge_thresh)
    return near_left_edge or near_right_edge

def dynamic_merge_threshold(image):
    w, h = image.size
    if max(w, h) >= 2500:
        return 8
    elif max(w, h) >= 1600:
        return 10
    else:
        return 15
def getSortedLikeCalendar(all_boxes=None, y_thresh=8):
    if not all_boxes:
        return []

    all_boxes = sorted(all_boxes, key=lambda box: (box[1], box[0]))  # sort top to bottom, then left to right

    rows = []
    current_row = []
    anchor_y = all_boxes[0][1]  # fixed anchor for the row

    for box in all_boxes:
        y1 = box[1]
        if abs(y1 - anchor_y) < y_thresh:
            current_row.append(box)
        else:
            rows.append(sorted(current_row, key=lambda b: b[0]))  # sort row left to right
            current_row = [box]
            anchor_y = y1  # reset anchor for new row

    if current_row:
        rows.append(sorted(current_row, key=lambda b: b[0]))


    return rows

def merge_partial_boxes_once(partial_rows, full_boxes=None, y_thresh=8, x_thresh=20, text_entry=None, test_mode=False):
    if not partial_rows:
        return []

    # 🔢 Calculate average full box area
    avg_full_area = None
    if full_boxes:
        areas = [(x2 - x1) * (y2 - y1) for x1, y1, x2, y2, *_ in full_boxes]
        avg_full_area = np.mean(areas) if areas else None

    merged_boxes = []

    for row in partial_rows:
        i = 0
        while i < len(row):
            box1 = row[i]
            x1, y1, x2, y2, cls1 = box1[:5]
            conf1 = box1[5] if len(box1) >= 6 else 1.0

            if i + 1 < len(row):
                box2 = row[i + 1]
                x1b, y1b, x2b, y2b, cls2 = box2[:5]
                conf2 = box2[5] if len(box2) >= 6 else 1.0

                h_gap = x1b - x2
                v_overlap = min(y2, y2b) - max(y1, y1b)

                if -15 <= h_gap <= 15 and v_overlap > -y_thresh:
                    conf1_biased = conf1 + 0.2
                    use_left = conf1_biased >= conf2
                    base = box1 if use_left else box2
                    other = box2 if use_left else box1

                    x1c, y1c, x2c, y2c, cls_final = base[:5]
                    x1o, y1o, x2o, y2o = other[:4]
                    conf_final = max(conf1, conf2)

                    merged_box = (
                        min(x1c, x1o),
                        min(y1c, y1o),
                        max(x2c, x2o),
                        max(y2c, y2o),
                        cls_final,
                        conf_final,
                    )

                    if avg_full_area:
                        merged_area = (merged_box[2] - merged_box[0]) * (merged_box[3] - merged_box[1])
                        if merged_area > 1.6 * avg_full_area:
                            if text_entry and test_mode:
                                text_entry.insert("end", f"🚫 Skipped merge (too large): {merged_area:.0f} > {avg_full_area:.0f}\n")
                                text_entry.see("end")
                            merged_boxes.append(box1)
                            i += 1
                            continue

                    merged_boxes.append(merged_box)
                    if text_entry and test_mode:
                        text_entry.insert("end", f"🟢 Merged: {conf1:.2f}+0.2 vs {conf2:.2f}\n")
                        text_entry.see("end")
                    i += 2  # ✅ Skip both merged boxes
                    continue

                elif h_gap < 0 and v_overlap > -y_thresh:
                    shift_amount = abs(h_gap) + 5
                    x1b += shift_amount
                    x2b += shift_amount
                    row[i + 1] = (x1b, y1b, x2b, y2b, cls2, conf2)

                    if text_entry and test_mode:
                        text_entry.insert("end", f"🟡 Shifted {box2} → {row[i+1]} by {shift_amount}px\n")
                        text_entry.see("end")

            # ❗ Only add if no merge occurred
            merged_boxes.append((x1, y1, x2, y2, cls1, conf1))
            i += 1

    return merged_boxes




def merge_boxes(all_boxes, test_mode=False):
    all_rows = getSortedLikeCalendar(all_boxes=all_boxes)
    full_boxes = []
    partial_rows = []

    for row in all_rows:
        row.sort(key=lambda box: box[0])  # sort left-to-right by x1
        partial_row = []
        for box in row:
            x1, y1, x2, y2, cls, conf = box[:6]
            if crosses_tile_edge(x1, x2):
                partial_row.append(box)
            else:
                full_boxes.append(box)

        if partial_row:
            partial_rows.append(partial_row)

    return full_boxes, partial_rows  # ← add all_rows here if you want full calendar view


def draw_boxes(image_cv, boxes, color=(0, 255, 0), test_mode=False, classes=None):
    if not test_mode:
        return

    for box in boxes:
        if len(box) >= 5:
            x1, y1, x2, y2, cls = box[:5]
        else:
            x1, y1, x2, y2 = box
            cls = -1


        # Draw the rectangle
        cv2.rectangle(image_cv, (x1, y1), (x2, y2), color, 1)

        # Draw class name text
        if classes is not None and 0 <= cls < len(classes):
            label = classes[cls]
        else:
            label = "unknown"

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        font_thickness = 1
        text_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]

        # Make sure text is inside image
        text_x = x1
        text_y = y1 - 5 if y1 - 5 > 10 else y1 + 15

        cv2.putText(
            image_cv,
            label,
            (text_x, text_y),
            font,
            font_scale,
            (0, 255, 0),
            font_thickness,
            cv2.LINE_AA,
        )


