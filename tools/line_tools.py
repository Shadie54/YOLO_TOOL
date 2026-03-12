# line_tools.py
import cv2
from tools.point_tool_base import PointToolBase  # predpokladáme, že Base je v point_tool_base.py

class PolylineTool(PointToolBase):
    """Polyline nástroj: kreslí sériu rovnakých priamok, s preview bodom"""

    def __init__(self, log_callback=None, brush_size=3, brush_color=(0, 0, 0)):
        super().__init__(log_callback=log_callback)
        self.brush_size = brush_size
        self.brush_color = brush_color

    def draw(self, img, zoom=1.0, preview=True, draw_points=True):
        """Nakreslí priamky medzi bodmi a preview bod (ak existuje)"""
        pts = self.points.copy()
        if preview and self.preview_point:
            pts.append(self.preview_point)

        if len(pts) < 2:
            # len preview bod
            if self.preview_point and draw_points:
                px, py = int(self.preview_point[0] * zoom), int(self.preview_point[1] * zoom)
                cv2.circle(img, (px, py), 4, (0, 0, 255), -1)
            return

        # kreslenie všetkých segmentov
        for i in range(len(pts) - 1):
            x1, y1 = int(pts[i][0] * zoom), int(pts[i][1] * zoom)
            x2, y2 = int(pts[i + 1][0] * zoom), int(pts[i + 1][1] * zoom)
            cv2.line(img, (x1, y1), (x2, y2), self.brush_color, self.brush_size)

        # červené body pre všetky uložené body (iba ak draw_points=True)
        if draw_points:
            for p in self.points:
                px, py = int(p[0] * zoom), int(p[1] * zoom)
                cv2.circle(img, (px, py), 4, (0, 0, 255), -1)

    def finalize(self, img):
        """Nakreslí polyline na finálny obrázok bez červených bodov a vyčistí body"""
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