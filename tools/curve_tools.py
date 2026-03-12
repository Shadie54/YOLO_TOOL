# curve_tools.py

import cv2
import numpy as np
from tools.tool_types import ToolType

class CurveTool:
    """Jednoduchá 3-bodová krivka"""
    def __init__(self, log_callback=None, brush_size=3, brush_color=(0, 0, 0)):
        self.points = []
        self.preview_point = None
        self.brush_size = brush_size
        self.brush_color = brush_color
        self.log_callback = log_callback

    def start_point(self, x, y):
        self.points = [(x, y)]
        self._log(f"Curve start at {(x, y)}")

    def add_point(self, x, y):
        self.points.append((x, y))
        self._log(f"Curve point added at {(x, y)}")

    def set_preview(self, x, y):
        self.preview_point = (x, y)
        self._log(f"Curve preview at {(x, y)}")

    def draw(self, img, zoom=1.0, preview=True):

        pts = self.points.copy()

        if preview and self.preview_point:
            pts.append(self.preview_point)

        if len(pts) < 2:
            # zobraz preview bod ešte pred prvým kliknutím
            if preview and self.preview_point:
                px = int(self.preview_point[0] * zoom)
                py = int(self.preview_point[1] * zoom)
                cv2.circle(img, (px, py), 4, (0, 0, 255), -1)
            return

        # kreslenie segmentov
        for i in range(len(pts) - 1):
            x1 = int(pts[i][0] * zoom)
            y1 = int(pts[i][1] * zoom)

            x2 = int(pts[i + 1][0] * zoom)
            y2 = int(pts[i + 1][1] * zoom)

            cv2.line(img, (x1, y1), (x2, y2), self.brush_color, self.brush_size)

        # červené body
        for p in self.points:
            px = int(p[0] * zoom)
            py = int(p[1] * zoom)
            cv2.circle(img, (px, py), 4, (0, 0, 255), -1)

    def undo_last_point(self):
        if self.points:
            removed = self.points.pop()
            self._log(f"Curve undo last point {removed}")

    def finalize(self, img):
        if len(self.points) < 2:
            return
        for i in range(len(self.points) - 1):
            cv2.line(img, self.points[i], self.points[i + 1], self.brush_color, self.brush_size)
        self.points.clear()
        self.preview_point = None

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[Curve] {msg}")


class PolyCurveTool:
    """PolyCurve s Catmull-Rom spline a neobmedzeným počtom bodov"""
    def __init__(self, log_callback=None, brush_size=3, brush_color=(0, 0, 0)):
        self.points = []
        self.preview_point = None
        self.brush_size = brush_size
        self.brush_color = brush_color
        self.log_callback = log_callback

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

    def start_point(self, x, y):
        self.points = [(x, y)]
        self._log(f"PolyCurve start at {(x, y)}")

    def add_point(self, x, y):
        self.points.append((x, y))
        self._log(f"PolyCurve point added at {(x, y)}")

    def set_preview(self, x, y):
        self.preview_point = (x, y)
        self._log(f"PolyCurve preview at {(x, y)}")

    def undo_last_point(self):
        if self.points:
            removed = self.points.pop()
            self._log(f"PolyCurve undo last point {removed}")

    def draw(self, img, zoom=1.0, preview=True):
        """Nakreslí body + spline na obrázok s preview bodom"""
        pts = self.points.copy()

        # pridáme preview bod, ak je
        if preview and self.preview_point:
            pts.append(self.preview_point)

        # ak máme len 1 bod, vykreslíme len preview bod a vrátime sa
        if len(pts) < 2:
            if preview and self.preview_point:
                px = int(self.preview_point[0] * zoom)
                py = int(self.preview_point[1] * zoom)
                cv2.circle(img, (px, py), 4, (0, 0, 255), -1)
            return

        # 2 body -> priamka
        if len(pts) == 2:
            x1, y1 = int(pts[0][0] * zoom), int(pts[0][1] * zoom)
            x2, y2 = int(pts[1][0] * zoom), int(pts[1][1] * zoom)
            cv2.line(img, (x1, y1), (x2, y2), self.brush_color, self.brush_size)
        else:
            # Catmull-Rom pre 3+ body
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

        # červené body (len originálne body, preview je už zahrnutý vyššie)
        for p in self.points:
            px = int(p[0] * zoom)
            py = int(p[1] * zoom)
            cv2.circle(img, (px, py), 4, (0, 0, 255), -1)

    def finalize(self, img):
        # nakreslí len spline, preview a červené body sa neprepisujú
        if len(self.points) < 2:
            return
        # 2 body -> priamka
        if len(self.points) == 2:
            cv2.line(img, self.points[0], self.points[1], self.brush_color, self.brush_size)
        else:
            # Catmull-Rom pre 3+ body
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

        # clear points, preview
        self.points.clear()
        self.preview_point = None

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(f"[PolyCurve] {msg}")