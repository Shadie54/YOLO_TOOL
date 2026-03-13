import cv2
from tools.point_tool_base import PointToolBase
from tools.tool_types import ToolType

# ------------------------- LINE TOOL -------------------------
class LineTool(PointToolBase):

    def __init__(self, log_callback=None, brush_size=3):
        super().__init__(log_callback=log_callback, brush_size=brush_size)
        self.start_point = None
        self.end_point = None
        self.tool_type = ToolType.LINE

    def start_point_line(self, x, y):
        self.start_point = (x, y)
        self.preview_point = (x, y)
        self.points = [(x, y)]  # jednotné použitie points pre dispatcher

    def add_point_line(self, x, y):
        if self.start_point:
            self.end_point = (x, y)
            self.points.append((x, y))

    def set_preview(self, x, y):
        if self.start_point and not self.end_point:
            self.preview_point = (x, y)

    def draw(self, img, zoom=1.0):
        # LINE preview / finálna
        if self.start_point:
            sx, sy = int(self.start_point[0] * zoom), int(self.start_point[1] * zoom)

            if self.end_point:
                ex, ey = int(self.end_point[0] * zoom), int(self.end_point[1] * zoom)
                cv2.line(img, (sx, sy), (ex, ey), (0, 0, 0), self.brush_size, cv2.LINE_8)
            elif self.preview_point:
                ex, ey = int(self.preview_point[0] * zoom), int(self.preview_point[1] * zoom)
                cv2.line(img, (sx, sy), (ex, ey), (0, 0, 0), self.brush_size, cv2.LINE_8)
                cv2.circle(img, (ex, ey), 4, (0, 0, 255), -1)

            # červený bod štartu navrchu
            cv2.circle(img, (sx, sy), 4, (0, 0, 255), -1)
        elif self.preview_point:
            px, py = int(self.preview_point[0] * zoom), int(self.preview_point[1] * zoom)
            cv2.circle(img, (px, py), 4, (0, 0, 255), -1)

    def finalize(self, img):
        if self.start_point and self.end_point:
            cv2.line(img, self.start_point, self.end_point, (0, 0, 0), self.brush_size, cv2.LINE_8)
            self._log(f"Line drawn from {self.start_point} to {self.end_point}")
        self.start_point = None
        self.end_point = None
        self.preview_point = None
        self.points.clear()

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[Line] {msg}")

# ------------------------- POLYLINE TOOL -------------------------
class PolylineTool(PointToolBase):

    def __init__(self, log_callback=None, brush_size=3, brush_color=(0, 0, 0)):
        super().__init__(log_callback=log_callback)
        self.brush_size = brush_size
        self.brush_color = brush_color
        self.tool_type = ToolType.POLYLINE

    def draw(self, img, zoom=1.0, preview=True, draw_points=True):
        pts = self.points.copy()
        if preview and self.preview_point:
            pts.append(self.preview_point)

        if len(pts) < 1:
            if self.preview_point and draw_points:
                px, py = int(self.preview_point[0] * zoom), int(self.preview_point[1] * zoom)
                cv2.circle(img, (px, py), 4, (0, 0, 255), -1)
            return

        # kreslí všetky segmenty
        for i in range(len(pts) - 1):
            x1, y1 = int(pts[i][0] * zoom), int(pts[i][1] * zoom)
            x2, y2 = int(pts[i + 1][0] * zoom), int(pts[i + 1][1] * zoom)
            cv2.line(img, (x1, y1), (x2, y2), self.brush_color, self.brush_size)

        # červené body pre uložené body
        if draw_points:
            for p in self.points:
                px, py = int(p[0] * zoom), int(p[1] * zoom)
                cv2.circle(img, (px, py), 4, (0, 0, 255), -1)

        # preview bod navrchu
        if preview and self.preview_point:
            px, py = int(self.preview_point[0] * zoom), int(self.preview_point[1] * zoom)
            cv2.circle(img, (px, py), 4, (0, 0, 255), -1)

    def finalize(self, img):
        pts = self.points
        if len(pts) < 2:
            self.points.clear()
            self.preview_point = None
            return

        for i in range(len(pts) - 1):
            x1, y1 = int(pts[i][0]), int(pts[i][1])
            x2, y2 = int(pts[i + 1][0]), int(pts[i + 1][1])
            cv2.line(img, (x1, y1), (x2, y2), self.brush_color, self.brush_size)

        self.points.clear()
        self.preview_point = None
        self._log("Polyline finalized")

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[Polyline] {msg}")