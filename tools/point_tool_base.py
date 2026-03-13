#point_tool_base.py
import cv2
class PointToolBase:

    def __init__(self, log_callback=None, brush_size=3, brush_color=(0,0,0)):
        self.points = []
        self.preview_point = None
        self.brush_size = brush_size
        self.brush_color = brush_color
        self.log_callback = log_callback

    def start_point(self, x, y):
        self.points = [(x,y)]

    def add_point(self, x, y):
        self.points.append((x,y))

    def set_preview(self, x, y):
        self.preview_point = (x,y)

    def undo_last_point(self):
        """Zruší posledný bod alebo preview bod"""
        if self.preview_point:
            self.preview_point = None
            self.end_point = None
            self._log("Preview point cancelled")
        elif self.points:
            self.points.pop()
            self._log("Start point removed")

    def draw_points(self, img, zoom):
        for p in self.points:
            px = int(p[0] * zoom)
            py = int(p[1] * zoom)
            cv2.circle(img,(px,py),4,(0,0,255),-1)

    def draw_preview_point(self, img, zoom):
        if self.preview_point:
            px = int(self.preview_point[0] * zoom)
            py = int(self.preview_point[1] * zoom)
            cv2.circle(img,(px,py),3,(0,0,255),-1)