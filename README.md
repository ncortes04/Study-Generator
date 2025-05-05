# 📅 Study-Generator

## Overview

The Study Planner Assistant is a fully automated tool that captures, detects, interprets, and summarizes academic calendars using YOLO-based object detection, OCR, and GPT reasoning. Built for Canvas-style calendar screenshots, this system identifies assignments, groups them by day, and generates personalized study plans.

---

## 🧠 Key Features

- **YOLOv5 object detection model** trained on calendar event boxes.
- **OCR pipeline** for extracting readable text from detected assignment boxes.
- **GPT integration** to summarize events and suggest prioritized study strategies.
- **Custom HTML generator** that renders synthetic calendar views to generate a diverse, high-volume dataset.
- **Real-time screenshot capture + UI overlay** for seamless user interaction.

---

## 🔍 Dataset Generation

### 📄 Synthetic Calendar Generator

The `generator.js` file (Node.js + Puppeteer + Sharp) dynamically renders HTML versions of the Canvas calendar using randomly chosen:

- Event labels (assignments, classes, to-dos, etc.)
- Colors and layout styles
- Icons associated with different task types
- Viewports (mobile, tablet, laptop, desktop)
- Gaussian blur, cropping, resolution scaling

This produced **thousands of training samples** with embedded YOLOv5 `.txt` labels in the YOLO format, enabling rapid augmentation and model iteration.

> 📸 See `BTS image preprossessing.png` for raw vs. processed renderings

---

## 🧪 Model Training & Fine-Tuning

The object detector was trained using **YOLOv5** across several rounds of experimentation:

- **Backbone**: YOLOv5s
- **Custom classes**: `todo`, `assignment`, `discussion`, `class`
- **Initial epochs**: 30, later extended up to **200+ with early stopping**
- **Fine-tuning**: Over **30 refinements** adjusting label overlap handling, class balancing, and augmentations
- **Validation**: Manual review of precision vs. recall in cropped segments

> 🔁 Mistakes like "double-detection" or "misaligned boxes" were solved using tile-splitting + dynamic merging logic.

---

## 🧾 YOLOv5 Label Workflow

Each image was split into tiles (for higher recall in dense views), then recombined using:

- `split_into_tiles()`
- `merge_partial_boxes_once()`
- `remove_duplicate_boxes()`

Boxes were then passed to `extract_text_from_box()` for Tesseract OCR.

---

## 🤖 GPT Integration

After all boxes are extracted and grouped by day using `group_boxes_by_grid()` and `organize_calendar_entries()`, the full calendar is compiled into a string prompt like:

```
📅 Day 1:
  - [assignment] WebHW14.6
  - [class] TMATH 126A Sp 25
📅 Day 2:
  - ...
```

This prompt is sent to `ask_gpt()` which calls GPT-4o to generate:

- A **study plan breakdown**
- **Task prioritization**
- **Clarification suggestions** for ambiguous or duplicate entries

> 🧠 See `chat_example.png` for a real response.

---

## 🖥️ User Interface

The UI (`tkinter`) includes:

- Screenshot monitoring (`watch_clipboard`)
- Event highlighting
- GPT chat integration
- Auto-scroll and logging

---

## 🧩 Tech Stack

- `YOLOv5` (Ultralytics) – detection
- `Pytesseract` – OCR
- `OpenAI API` – GPT-4o reasoning
- `Node.js + Puppeteer + Sharp` – image generation
- `Tkinter` – UI
- `PIL + OpenCV` – image manipulation

---

## 🏁 Future Improvements

- Add bounding box classification confidence thresholds
- Export study suggestions to `.md` or `.ics`
- Enable drag-and-drop screenshot uploads
- Visual grouping by subject or priority

---

## 🙌 Credits

Project by **Nicholas Cortes**  
Inspired by real struggles with Canvas calendar overload 😅
