import cv2
from tools.tool_types import ToolType

class DrawingEngine:
    def __init__(self, cv_img=None, log_callback=None):
        self.cv_img = cv_img
        self.brush_size = 3
        self.brush_color = (0, 0, 0)
        self.tool = None  # freehand / line / white

        self.drawing = False
        self.start_point = None
        self.line_start = None
        self.preview_line = None

        self.curve_points = []  # zoznam bodov pre CURVE
        self.polycurve_points = []  # zoznam bodov pre POLYCURVE
        self.preview_point = None  # bod pre vizualizáciu pohybu myši

        self.log_callback = log_callback

    # ------------------------- DRAWING -------------------------
    def start_draw(self, x, y):
        self.drawing = True
        if self.tool in [ToolType.FREEHAND, ToolType.WHITE]:
            self.start_point = (x, y)
            self._log(f"Start {self.tool} at {self.start_point}")

        elif self.tool == ToolType.LINE:
            self.line_start = (x, y)
            self.preview_line = (self.line_start, self.line_start)
            self._log(f"Line start at {self.line_start}")

        elif self.tool == ToolType.CURVE:
            self.curve_points = [(x, y)]
            self.preview_point = (x, y)
            self._log(f"Curve start at {(x, y)}")

        elif self.tool == ToolType.POLYCURVE:
            self.polycurve_points = [(x, y)]
            self.preview_point = (x, y)
            self._log(f"PolyCurve start at {(x, y)}")

    def move_draw(self, x, y):
        if not self.drawing or self.tool is None or self.cv_img is None:
            return

        if self.tool in [ToolType.FREEHAND, ToolType.WHITE]:
            color = self.brush_color if self.tool == ToolType.FREEHAND else (255, 255, 255)
            cv2.line(self.cv_img, self.start_point, (x, y), color, self.brush_size, cv2.LINE_8)
            self.start_point = (x, y)
            self._log(f"{self.tool} at {self.start_point}")

        elif self.tool == ToolType.LINE:
            if self.line_start is None:
                return
            self.preview_line = (self.line_start, (x, y))
            self._log(f"Preview line updated: {self.preview_line}")

        elif self.tool == ToolType.CURVE and self.curve_points:
            self.preview_point = (x, y)
            self._log(f"Curve preview at {(x, y)}")

        elif self.tool == ToolType.POLYCURVE and self.polycurve_points:
            self.preview_point = (x, y)
            self._log(f"PolyCurve preview at {(x, y)}")

    def end_draw(self, x, y):
        if not self.drawing or self.tool is None:
            return

        if self.tool == ToolType.LINE:
            cv2.line(self.cv_img, self.line_start, (x, y), self.brush_color, self.brush_size, cv2.LINE_8)
            self.preview_line = None
            self._log(f"Line end at {(x, y)}")

        elif self.tool == ToolType.CURVE:
            self.curve_points.append((x, y))
            self.preview_point = None
            self._log(f"Curve point added at {(x, y)}")
            # drawing zostáva True, kým užívateľ nepotvrdí ENTER alebo ESC

        elif self.tool == ToolType.POLYCURVE:
            self.polycurve_points.append((x, y))
            self.preview_point = None
            self._log(f"PolyCurve point added at {(x, y)}")
            # drawing zostáva True, až kým užívateľ nepotvrdí alebo nezruší

        # Reset pre freehand a line
        if self.tool in [ToolType.FREEHAND, ToolType.WHITE, ToolType.LINE]:
            self.drawing = False
            self.start_point = None
            self.line_start = None

    # ------------------------- LOG -------------------------
    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[DRAW] {msg}")