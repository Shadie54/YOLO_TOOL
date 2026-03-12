# curve_tools.py
import cv2
import numpy as np
from tools.point_tool_base import PointToolBase  # dedíme PointToolBase
from tools.tool_types import ToolType

class CurveTool(PointToolBase):
    """Jednoduchá 3-bodová krivka"""

    def __init__(self, log_callback=None, brush_size=3, brush_color=(0, 0, 0)):
        super().__init__(log_callback=log_callback, brush_size=brush_size, brush_color=brush_color)

    def draw(self, img, zoom=1.0, preview=True):
        pts = self.points.copy()
        if preview and self.preview_point:
            pts.append(self.preview_point)

        if len(pts) < 2:
            self.draw_preview_point(img, zoom)
            return

        # kreslenie všetkých segmentov
        for i in range(len(pts) - 1):
            x1, y1 = int(pts[i][0] * zoom), int(pts[i][1] * zoom)
            x2, y2 = int(pts[i + 1][0] * zoom), int(pts[i + 1][1] * zoom)
            cv2.line(img, (x1, y1), (x2, y2), self.brush_color, self.brush_size)

        # len originálne body (preview nie)
        self.draw_points(img, zoom)

    def finalize(self, img):
        if len(self.points) < 2:
            self.points.clear()
            self.preview_point = None
            return

        for i in range(len(self.points) - 1):
            cv2.line(img, self.points[i], self.points[i + 1], self.brush_color, self.brush_size)

        self.points.clear()
        self.preview_point = None
        self._log("Curve finalized")

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[Curve] {msg}")


class PolyCurveTool(PointToolBase):
    """PolyCurve s Catmull-Rom spline a neobmedzeným počtom bodov"""

    def __init__(self, log_callback=None, brush_size=3, brush_color=(0, 0, 0)):
        super().__init__(log_callback=log_callback, brush_size=brush_size, brush_color=brush_color)

    @staticmethod
    def catmull_rom(p0, p1, p2, p3, t):
        t2 = t * t
        t3 = t2 * t
        return 0.5 * (
            (2 * p1)
            + (-p0 + p2) * t
            + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
            + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
        )

    def draw(self, img, zoom=1.0, preview=True):
        pts = self.points.copy()
        if preview and self.preview_point:
            pts.append(self.preview_point)

        if len(pts) < 2:
            self.draw_preview_point(img, zoom)
            return

        if len(pts) == 2:
            # len priamka
            x1, y1 = int(pts[0][0] * zoom), int(pts[0][1] * zoom)
            x2, y2 = int(pts[1][0] * zoom), int(pts[1][1] * zoom)
            cv2.line(img, (x1, y1), (x2, y2), self.brush_color, self.brush_size)
        else:
            # Catmull-Rom spline pre 3+ body
            p = [pts[0]] + pts + [pts[-1]]
            for i in range(len(p) - 3):
                p0 = np.array(p[i])
                p1 = np.array(p[i + 1])
                p2 = np.array(p[i + 2])
                p3 = np.array(p[i + 3])
                prev = None
                for t in np.linspace(0, 1, 50):
                    pt = self.catmull_rom(p0, p1, p2, p3, t)
                    pt = (int(pt[0] * zoom), int(pt[1] * zoom))
                    if prev is not None:
                        cv2.line(img, prev, pt, self.brush_color, self.brush_size)
                    prev = pt

        # len originálne body
        self.draw_points(img, zoom)

    def finalize(self, img):
        if len(self.points) < 2:
            self.points.clear()
            self.preview_point = None
            return

        if len(self.points) == 2:
            cv2.line(img, self.points[0], self.points[1], self.brush_color, self.brush_size)
        else:
            pts = [self.points[0]] + self.points + [self.points[-1]]
            prev = None
            for i in range(len(pts) - 3):
                p0 = np.array(pts[i])
                p1 = np.array(pts[i + 1])
                p2 = np.array(pts[i + 2])
                p3 = np.array(pts[i + 3])
                for t in np.linspace(0, 1, 50):
                    pt = self.catmull_rom(p0, p1, p2, p3, t)
                    pt = (int(pt[0]), int(pt[1]))
                    if prev is not None:
                        cv2.line(img, prev, pt, self.brush_color, self.brush_size)
                    prev = pt

        self.points.clear()
        self.preview_point = None
        self._log("PolyCurve finalized")

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[PolyCurve] {msg}")