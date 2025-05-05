from ocr.exctract import extract_text_from_box
from ocr.getgrid import group_boxes_by_grid, organize_calendar_entries, draw_grouped_boxes
from ocr.screenshot_watcher import watch_clipboard
from ocr.yolodetector import run_yolo_on_pil_image, remove_duplicate_boxes
from ocr.tile_merging import split_into_tiles, dynamic_merge_threshold, merge_boxes, merge_partial_boxes_once, draw_boxes
from ui.window import create_ui
from Appstate import AppState
from PIL import Image, ImageGrab
import numpy as np
from gpt.chatgptAPI import ask_gpt
import cv2
from dotenv import load_dotenv
import tkinter as tk

test_mode = True

classes = ["todo", "discussion", "class", "assignment"]
def on_assignments_detected(_):
    global text_entry

    image = ImageGrab.grabclipboard()
    if image is None or not isinstance(image, Image.Image):
        print("❌ No image found on clipboard")
        return

    text_entry.configure(state="normal")
    text_entry.insert("end", "🧑‍🎓 Detecting Assignments...\n")

    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    tiles = split_into_tiles(image)
    dynamic_y_thresh = dynamic_merge_threshold(image)

    all_boxes = []
    raw_yolo_detections = 0

    for tile_idx, (tile, (offset_x, offset_y)) in enumerate(tiles):
        
        results = run_yolo_on_pil_image(tile)


        # if test_mode:
        #     tile_cv = cv2.cvtColor(np.array(tile), cv2.COLOR_RGB2BGR)
        #     for box in results.xyxy[0].cpu().numpy():
        #         x1, y1, x2, y2, conf, cls = box[:6]
        #         cv2.rectangle(tile_cv, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        #         label = classes[int(cls)] if int(cls) < len(classes) else "unknown"
        #         cv2.putText(
        #             tile_cv, 
        #             label, 
        #             (int(x1), int(y1) - 10),  # 🧠 slightly above the box
        #             cv2.FONT_HERSHEY_SIMPLEX, 
        #             0.5, 
        #             (0, 255, 0), 
        #             1, 
        #             cv2.LINE_AA
        #         )
        #     cv2.imshow(f"Tile {tile_idx}", tile_cv)


        raw_yolo_detections += len(results.xyxy[0])

        for box in results.xyxy[0].cpu().numpy():
            x1, y1, x2, y2, conf, cls = box[:6]
            x1_full = int(x1 + offset_x)
            y1_full = int(y1 + offset_y)
            x2_full = int(x2 + offset_x)
            y2_full = int(y2 + offset_y)
            if (x2_full - x1_full) > 15 and (y2_full - y1_full) > 15:
                all_boxes.append((x1_full, y1_full, x2_full, y2_full, int(cls), float(conf)))

    if test_mode:
        print(f"\n🧹 Before deduplication: {len(all_boxes)} boxes")
        print(f"🧹 Total YOLO raw detections: {raw_yolo_detections}")

    all_boxes = remove_duplicate_boxes(all_boxes)

    if test_mode:
        print(f"🧹 After deduplication: {len(all_boxes)} boxes\n")

    full_boxes, partial_boxes = merge_boxes(all_boxes, test_mode=test_mode)

    merged_partial_boxes = merge_partial_boxes_once(partial_boxes, full_boxes=full_boxes,y_thresh=dynamic_y_thresh, text_entry=text_entry, test_mode=test_mode)

    final_boxes = full_boxes + merged_partial_boxes
    all_classes_detected = []

    # 🧠 Collect text+class here
    final_results = []

    for box in final_boxes:
        x1, y1, x2, y2, cls, conf = box[:6]
        class_label = classes[cls] if cls < len(classes) else "Unknown"
        extracted_text = extract_text_from_box(image_cv, (x1, y1, x2, y2))

        final_results.append((class_label, extracted_text))
        all_classes_detected.append(class_label)


    draw_boxes(image_cv, final_boxes, color=(0, 255, 0), test_mode=test_mode, classes=classes)

    text_entry.insert("end", f"\n✅ Final event boxes drawn: {len(final_boxes)}\n\n")

    # # 🔥 Now actually insert all box results into the UI
    # for class_label, extracted_text in final_results:
    #     line = f"[{class_label}]: {extracted_text}\n"
    #     text_entry.insert("end", line)

    # text_entry.configure(state="disabled")
    # text_entry.see("end")

    # # ✅ Log also in console
    # print(f"📚 Detected Classes and Texts:")
    # for class_label, extracted_text in final_results:
    #     print(f"✅ [{class_label}]: {extracted_text}")


    # text_entry.configure(state="disabled")
    # text_entry.see("end")
    # Flatten the already-sorted rows
    groups = group_boxes_by_grid(final_boxes)
    calendar = organize_calendar_entries(groups, image_cv, classes)



#     # 📤 Format the calendar into a string for GPT
#     calendar_summary = ""
#     for i, day in enumerate(calendar, 1):
#         calendar_summary += f"📅 Day {i}:\n"
#         for class_label, text in day:
#             calendar_summary += f"  - [{class_label}] {text.strip()}\n"

#     if not calendar_summary.strip():
#         text_entry.insert("end", "\n⚠️ No assignment text found to send to GPT.\n")
#         text_entry.see("end")
#         return

#     # 💬 Send to GPT for processing
#     gpt_prompt = f"""Here is a calendar of upcoming tasks by day:\n\n{calendar_summary}
# Please review and suggest a study plan that prioritizes harder or urgent tasks. Also highlight if anything looks like a duplicate or unclear."""

#     text_entry.insert("end", "\n🤖 Asking GPT to review calendar...\n")
#     text_entry.see("end")

#     try:
#         gpt_response, _ = ask_gpt(gpt_prompt)
#         text_entry.insert("end", f"\n🧠 GPT's Study Suggestion:\n{gpt_response}\n")
#     except Exception as e:
#         text_entry.insert("end", f"\n❌ GPT failed: {e}\n")

#     text_entry.see("end")


    # ✅ Log all detected classes
    # print(f"📚 Detected Classes: {all_classes_detected}")
    # print(f"📚 Detected Classes Length: {len(all_classes_detected)}")

    if test_mode:
        cv2.imshow("📸 Screenshot with Final Event Boxes", image_cv)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def on_input_enter(event):
    user_message = input_field.get().strip()
    if not user_message:
        return

    input_field.delete(0, tk.END)
    text_entry.configure(state="normal")
    text_entry.insert("end", f"\n🗣️ You: {user_message}\n")
    
    response, _ = ask_gpt(user_message)
    text_entry.insert("end", f"🤖 GPT: {response}\n")
    text_entry.configure(state="disabled")
    text_entry.see("end")


def on_close():
    exit()

app_state = AppState()
window, text_entry, input_field = create_ui(app_state, on_input_enter, on_close)
watch_clipboard(on_assignments_detected)
window.mainloop()
