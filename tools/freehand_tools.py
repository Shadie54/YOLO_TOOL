import cv2
from tools.point_tool_base import PointToolBase
from tools.tool_types import ToolType

# ------------------------- PENCIL TOOL -------------------------
class PencilTool(PointToolBase):

    def __init__(self, log_callback=None, brush_size=3, color=(0,0,0)):
        super().__init__(log_callback=log_callback, brush_size=brush_size)
        self.color = color
        self.tool_type = ToolType.PENCIL
        self.preview_point = None

    def add_point(self, x, y):
        self.points.append((x, y))
        self.preview_point = (x, y)  # update preview vždy

    def set_preview(self, x, y):
        self.preview_point = (x, y)

    def draw(self, img, zoom=1.0):
        # kreslenie liniek
        if len(self.points) > 1:
            for i in range(len(self.points)-1):
                x1, y1 = map(lambda v: int(v*zoom), self.points[i])
                x2, y2 = map(lambda v: int(v*zoom), self.points[i+1])
                cv2.line(img, (x1, y1), (x2, y2), self.color, self.brush_size)

        # preview kruhu
        if self.preview_point:
            px, py = map(lambda v: int(v*zoom), self.preview_point)
            cv2.circle(img, (px, py), self.brush_size, self.color, 1)

    def finalize(self, img):
        if len(self.points) < 2:
            self.points.clear()
            self.preview_point = None
            return
        for i in range(len(self.points)-1):
            cv2.line(img, self.points[i], self.points[i+1], self.color, self.brush_size)
        self.points.clear()
        self.preview_point = None
        self._log("Pencil stroke")

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[Pencil] {msg}")


# ------------------------- ERASER TOOL -------------------------
class EraserTool(PointToolBase):

    def __init__(self, log_callback=None, brush_size=10):
        super().__init__(log_callback=log_callback, brush_size=brush_size)
        self.tool_type = ToolType.ERASER
        self.color = (255, 255, 255)
        self.preview_point = None

    def add_point(self, x, y):
        self.points.append((x, y))
        self.preview_point = (x, y)  # update preview vždy

    def set_preview(self, x, y):
        self.preview_point = (x, y)

    def draw(self, img, zoom=1.0):
        # kreslenie liniek
        if len(self.points) > 1:
            for i in range(len(self.points)-1):
                x1, y1 = map(lambda v: int(v*zoom), self.points[i])
                x2, y2 = map(lambda v: int(v*zoom), self.points[i+1])
                cv2.line(img, (x1, y1), (x2, y2), self.color, self.brush_size)

        # preview kruhu
        if self.preview_point:
            px, py = map(lambda v: int(v*zoom), self.preview_point)
            # sivý kruh pre gumu
            cv2.circle(img, (px, py), self.brush_size, (120, 120, 120), 1)

    def finalize(self, img):
        if len(self.points) < 2:
            self.points.clear()
            self.preview_point = None
            return
        for i in range(len(self.points)-1):
            cv2.line(img, self.points[i], self.points[i+1], self.color, self.brush_size)
        self.points.clear()
        self.preview_point = None
        self._log("Erase stroke")

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[Eraser] {msg}")