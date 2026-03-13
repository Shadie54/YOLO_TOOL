#delete_tools.py
class DeleteTool:

    def __init__(self, canvas):
        self.canvas = canvas
        self.hover_box = None

    # -------------------------
    # Hover detection
    # -------------------------
    def hover(self, x, y, boxes):

        new_hover = None

        for i, (x1, y1, x2, y2, cls) in enumerate(boxes):
            if x1 <= x <= x2 and y1 <= y <= y2:
                new_hover = i
                break

        self.hover_box = new_hover
        return new_hover

    # -------------------------
    # Click detection
    # -------------------------
    def click(self, x, y, boxes):

        clicked = None

        for i, (x1, y1, x2, y2, cls) in enumerate(boxes):
            if x1 <= x <= x2 and y1 <= y <= y2:
                clicked = i
                break

        if clicked is not None:

            # odstránime box zo zoznamu
            x1, y1, x2, y2, cls = boxes.pop(clicked)

            # vrátime súradnice
            return (x1, y1, x2, y2, cls)

        return None