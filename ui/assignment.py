class DetectedAssignment:
    def __init__(self, class_name, text, box, color_category):
        self.class_name = class_name
        self.text = text
        self.box = box  # (x1, y1, x2, y2)
        self.color_category = color_category

    def __repr__(self):
        return f"[{self.color_category}] {self.class_name}: {self.text}"
