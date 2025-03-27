class AppState:
    def __init__(self):
        self.format = "calendar"
        self.user_input = ""
        self.history = []
        self.vars = {}
        self.boxes = {}

    def set_format(self, fmt):
        print(f"[AppState] Format changed: {self.format} → {fmt}")
        self.format = fmt
        self._update_checkboxes()

    def get_format(self):
        return self.format

    def _update_checkboxes(self):
        for key, var in self.vars.items():
            var.set(1 if key == self.format else 0)
