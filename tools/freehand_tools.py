# tools/freehand_tools.py
import cv2
from tools.point_tool_base import PointToolBase
from tools.tool_types import ToolType

# ------------------------- PENCIL TOOL -------------------------
class PencilTool(PointToolBase):

    def __init__(self, log_callback=None, brush_size=3, color=(0,0,0)):
        super().__init__(log_callback=log_callback, brush_size=brush_size)
        self.color = color
        self.tool_type = ToolType.PENCIL

    def add_point(self, x, y):
        self.points.append((x, y))

    def set_preview(self, x, y):
        self.preview_point = (x, y)

    def draw(self, img, zoom=1.0):

        # preview stroke
        if len(self.points) > 1:
            for i in range(len(self.points)-1):
                x1,y1 = self.points[i]
                x2,y2 = self.points[i+1]

                x1,y1 = int(x1*zoom), int(y1*zoom)
                x2,y2 = int(x2*zoom), int(y2*zoom)

                cv2.line(img,(x1,y1),(x2,y2),self.color,self.brush_size)

        # preview brush
        if self.preview_point:
            px,py = int(self.preview_point[0]*zoom), int(self.preview_point[1]*zoom)
            cv2.circle(img,(px,py),self.brush_size,self.color,1)

    def finalize(self, img):

        if len(self.points) < 2:
            self.points.clear()
            self.preview_point = None
            return

        for i in range(len(self.points)-1):
            cv2.line(
                img,
                self.points[i],
                self.points[i+1],
                self.color,
                self.brush_size
            )

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
        self.color = (255,255,255)

    def add_point(self, x, y):
        self.points.append((x, y))

    def set_preview(self, x, y):
        self.preview_point = (x, y)

    def draw(self, img, zoom=1.0):

        if len(self.points) > 1:
            for i in range(len(self.points)-1):
                x1,y1 = self.points[i]
                x2,y2 = self.points[i+1]

                x1,y1 = int(x1*zoom), int(y1*zoom)
                x2,y2 = int(x2*zoom), int(y2*zoom)

                cv2.line(img,(x1,y1),(x2,y2),self.color,self.brush_size)

        if self.preview_point:
            px,py = int(self.preview_point[0]*zoom), int(self.preview_point[1]*zoom)
            cv2.circle(img,(px,py),self.brush_size,(120,120,120),1)

    def finalize(self, img):

        if len(self.points) < 2:
            self.points.clear()
            self.preview_point = None
            return

        for i in range(len(self.points)-1):
            cv2.line(
                img,
                self.points[i],
                self.points[i+1],
                self.color,
                self.brush_size
            )

        self.points.clear()
        self.preview_point = None
        self._log("Erase stroke")

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[Eraser] {msg}")