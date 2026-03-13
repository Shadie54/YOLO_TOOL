#drawing_engine.py
import cv2
from tools.tool_types import ToolType

class DrawingEngine:
    def __init__(self, cv_img=None, log_callback=None):
        self.cv_img = cv_img
        self.brush_size = 3
        self.brush_color = (0, 0, 0)
        self.tool = None  # FREEHAND / LINE / WHITE

        self.drawing = False
        self.start_point = None
        self.line_start = None
        self.preview_line = None

        self.log_callback = log_callback

    # ------------------------- DRAWING -------------------------
    def start_draw(self, x, y):
        self.drawing = True
        if self.tool in [ToolType.PENCIL, ToolType.ERASER]:
            self.start_point = (x, y)
            self._log(f"Start {self.tool} at {self.start_point}")
        elif self.tool == ToolType.LINE:
            self.line_start = (x, y)
            self.preview_line = (self.line_start, self.line_start)
            self._log(f"Line start at {self.line_start}")

    def move_draw(self, x, y):
        if not self.drawing or self.tool is None or self.cv_img is None:
            return
        if self.tool in [ToolType.PENCIL, ToolType.ERASER]:
            color = self.brush_color if self.tool == ToolType.PENCIL else (255, 255, 255)
            cv2.line(self.cv_img, self.start_point, (x, y), color, self.brush_size, cv2.LINE_8)
            self.start_point = (x, y)
            self._log(f"{self.tool} at {self.start_point}")
        elif self.tool == ToolType.LINE and self.line_start is not None:
            self.preview_line = (self.line_start, (x, y))
            self._log(f"Preview line updated: {self.preview_line}")

    def end_draw(self, x, y):
        if not self.drawing or self.tool is None:
            return
        if self.tool == ToolType.LINE:
            cv2.line(self.cv_img, self.line_start, (x, y), self.brush_color, self.brush_size, cv2.LINE_8)
            self.preview_line = None
            self._log(f"Line end at {(x, y)}")
        # reset pre freehand a line
        if self.tool in [ToolType.PENCIL, ToolType.ERASER, ToolType.LINE]:
            self.drawing = False
            self.start_point = None
            self.line_start = None

    # ------------------------- LOG -------------------------
    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[DRAW] {msg}")