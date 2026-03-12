import cv2
import numpy as np
from tools.point_tool_base import PointToolBase


# ------------------------- LINE TOOL -------------------------
class LineTool(PointToolBase):
    """
    Jednoduchý 2-bodový line nástroj.
    Preview: červené bodky + čierna linka
    Finálna kresba: čierna linka
    """

    def __init__(self, log_callback=None, brush_size=3):
        super().__init__(log_callback=log_callback, brush_size=brush_size)
        self.points = []          # zoznam bodov (len 1 bod pre LINE)
        self.preview_point = None

    def start_point_line(self, x, y):
        """Začneme line nástroj"""
        self.points = [(x, y)]
        self.preview_point = (x, y)
        self._log(f"Line start at {(x,y)}")

    def add_point_line(self, x, y):
        """Druhý klik → finalize"""
        if len(self.points) == 1:
            self.points.append((x, y))   # druhý bod
        self.preview_point = None

    def set_preview(self, x, y):
        """Preview bod počas pohybu myši"""
        if self.points and len(self.points) == 1:
            self.preview_point = (x, y)

    def draw(self, img, zoom=1.0):
        """Nakreslí preview linku + červené body"""

        # preview bod pred prvým klikom
        if not self.points and self.preview_point:
            px, py = int(self.preview_point[0] * zoom), int(self.preview_point[1] * zoom)
            cv2.circle(img, (px, py), 4, (0, 0, 255), -1)
            return

        if not self.points:
            return

        pts = self.points.copy()
        if self.preview_point:
            pts.append(self.preview_point)

        # kreslenie linky
        if len(pts) >= 2:
            x1, y1 = int(pts[0][0] * zoom), int(pts[0][1] * zoom)
            x2, y2 = int(pts[1][0] * zoom), int(pts[1][1] * zoom)
            cv2.line(img, (x1, y1), (x2, y2), (0, 0, 0), self.brush_size)

        # červené body
        for p in self.points:
            px, py = int(p[0] * zoom), int(p[1] * zoom)
            cv2.circle(img, (px, py), 4, (0, 0, 255), -1)
            cv2.circle(img, (px, py), 4, (0, 0, 255), -1)

    def finalize(self, img):
        """Nakreslí finálnu linku a vyčistí body"""
        if len(self.points) == 2:
            cv2.line(img, self.points[0], self.points[1], (0,0,0), self.brush_size, cv2.LINE_8)
            self._log(f"Line drawn from {self.points[0]} to {self.points[1]}")
        self.points.clear()
        self.preview_point = None

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[Line] {msg}")

# ------------------------- POLYLINE TOOL -------------------------
class PolylineTool(PointToolBase):
    """Polyline nástroj: kreslí sériu rovnakých priamok, s preview bodom"""

    def __init__(self, log_callback=None, brush_size=3, brush_color=(0, 0, 0)):
        super().__init__(log_callback=log_callback)
        self.brush_size = brush_size
        self.brush_color = brush_color

    def draw(self, img, zoom=1.0, preview=True, draw_points=True):
        pts = self.points.copy()
        if preview and self.preview_point:
            pts.append(self.preview_point)

        if len(pts) < 2:
            if self.preview_point and draw_points:
                px, py = int(self.preview_point[0] * zoom), int(self.preview_point[1] * zoom)
                cv2.circle(img, (px, py), 4, (0, 0, 255), -1)
            return

        for i in range(len(pts) - 1):
            x1, y1 = int(pts[i][0] * zoom), int(pts[i][1] * zoom)
            x2, y2 = int(pts[i + 1][0] * zoom), int(pts[i + 1][1] * zoom)
            cv2.line(img, (x1, y1), (x2, y2), self.brush_color, self.brush_size)

        if draw_points:
            for p in self.points:
                px, py = int(p[0] * zoom), int(p[1] * zoom)
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

