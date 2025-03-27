from ui.window import create_ui
from ocr.screenshot_watcher import watch_clipboard
from ui.window import create_ui
from Appstate import AppState


def on_text_extracted_from_image(text):
    # Show the OCR result in the chat
    text_entry.configure(state="normal")
    text_entry.insert("end", "🖼️ Screenshot Detected:\n" + text + "\n\n")
    text_entry.configure(state="disabled")
    text_entry.see("end")

# Inside your setup logic
watch_clipboard(on_text_extracted_from_image)


def on_input_enter(event):
    pass

def on_close():
    exit()

app_state = AppState()

# Correct usage — pass app_state first
window, text_entry, input_field = create_ui(app_state, on_input_enter, on_close)
window.mainloop()

