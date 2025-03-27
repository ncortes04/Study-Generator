# ui/window.py
import customtkinter as ctk
import tkinter as tk
# Appearance settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Color scheme
BG_COLOR = "#1E1E1E"
TEXT_COLOR = "#E5E7EB"
ENTRY_COLOR = "#2C2C2E"
ACCENT_COLOR = "#3B82F6"
INACTIVE_COLOR = "#3A3A3C"
BORDER_COLOR = "#4B5563"


def create_checkbox(parent, text, value, app_state):
    var = tk.IntVar()

    def on_toggle():
        app_state.set_format(value)

    checkbox = ctk.CTkCheckBox(
        master=parent,
        text=text,
        command=on_toggle,
        variable=var,
        onvalue=1,
        offvalue=0,
        width=20,
        height=20,
        checkbox_width=20,
        checkbox_height=20,
        corner_radius=5,
        border_width=2,
        fg_color=ENTRY_COLOR,
        border_color=ACCENT_COLOR,
        hover_color=INACTIVE_COLOR,
        text_color=TEXT_COLOR,
        font=("Segoe UI", 13)
    )

    app_state.vars[value] = var
    app_state.boxes[value] = checkbox
    return checkbox


def create_ui(app_state, on_input_enter, on_close):
    def on_submit_click():
        user_input = input_field.get().strip()
        if user_input:
            app_state.input_text = user_input
            print("User submitted:", user_input)
            input_field.delete(0, tk.END)

    window = ctk.CTk()
    window.geometry('900x400')
    window.title("Study Planner Assistant")
    window.configure(bg=BG_COLOR)
    window.protocol("WM_DELETE_WINDOW", on_close)

    window.columnconfigure(0, weight=0)
    window.columnconfigure(1, weight=1)
    window.rowconfigure(0, weight=1)
    window.rowconfigure(1, weight=0)

    # === Format Options Sidebar ===
    radio_frame = ctk.CTkFrame(window, fg_color=BG_COLOR)
    radio_frame.grid(column=0, row=0, rowspan=2, sticky='nsew', padx=10, pady=10)

    calendar_cb = create_checkbox(radio_frame, "Calendar", "calendar", app_state)
    list_cb = create_checkbox(radio_frame, "List", "list", app_state)
    text_cb = create_checkbox(radio_frame, "Simple Text", "text", app_state)

    calendar_cb.pack(anchor="w", pady=5)
    list_cb.pack(anchor="w", pady=5)
    text_cb.pack(anchor="w", pady=5)

    # === Text Display ===
    text_entry = ctk.CTkTextbox(
        window,
        wrap=tk.WORD,
        font=('Arial', 16),
        fg_color=BG_COLOR,
        text_color=TEXT_COLOR,
        corner_radius=10
    )
    text_entry.grid(column=1, row=0, sticky='nsew', padx=10, pady=10)
    text_entry.insert("1.0", "\U0001F4CB Waiting for a screenshot...\n")
    text_entry.configure(state=tk.DISABLED)

    # === Input Field & Submit Button ===
    input_frame = ctk.CTkFrame(window)
    input_frame.grid(column=1, row=1, sticky='ew', padx=10, pady=(0, 10))
    input_frame.columnconfigure(0, weight=1)
    input_frame.columnconfigure(1, weight=0)

    input_field = ctk.CTkEntry(
        input_frame,
        placeholder_text="Type a message...",
        font=('Segoe UI', 15),
        fg_color=ENTRY_COLOR,
        text_color=TEXT_COLOR,
        border_color=ACCENT_COLOR,
        border_width=2,
        corner_radius=8
    )
    input_field.grid(column=0, row=0, sticky='ew', padx=(0, 10), pady=10)
    input_field.bind('<Return>', on_input_enter)

    submit_btn = ctk.CTkButton(
        input_frame,
        text="Submit",
        font=('Segoe UI Semibold', 14),
        fg_color=ACCENT_COLOR,
        text_color="white",
        hover_color="#2563EB",
        width=100,
        height=35,
        corner_radius=8,
        command=on_submit_click
    )
    submit_btn.grid(column=1, row=0, padx=(0, 10), pady=10)

    # === Credit Label ===
    credit_label = ctk.CTkLabel(
        window,
        text="By Nicholas Cortes",
        text_color=TEXT_COLOR,
        bg_color=BG_COLOR,
        font=('Arial', 10, 'italic')
    )
    credit_label.grid(column=1, row=2, sticky='se', padx=10, pady=(0, 5))

    return window, text_entry, input_field
