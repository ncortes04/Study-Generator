from ocr.exctract import extract_text_from_box

def group_events_by_day(boxes, tolerance=20):
    """
    Groups final_boxes by vertical position (y1) to simulate 'days' in calendar.
    """
    groups = []

    for box in boxes:
        x1, y1, x2, y2, cls = box[:5]
        matched = False
        for group in groups:
            if abs(group[0][1] - y1) <= tolerance:
                group.append((x1, y1, x2, y2, cls))
                matched = True
                break
        if not matched:
            groups.append([(x1, y1, x2, y2, cls)])

    print(f"✅ Grouped {len(boxes)} boxes into {len(groups)} day groups")
    return groups

def organize_calendar_entries(groups, image_cv, classes):
    results_by_day = []

    for group in sorted(groups, key=lambda g: g[0][1]):  # sort top-down
        day_entries = []
        for box in sorted(group, key=lambda b: b[0]):  # sort left-to-right
            x1, y1, x2, y2, cls = box
            class_label = classes[cls] if cls < len(classes) else "Unknown"
            extracted_text = extract_text_from_box(image_cv, (x1, y1, x2, y2))
            day_entries.append((class_label, extracted_text))
        results_by_day.append(day_entries)

    return results_by_day
