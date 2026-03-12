#image_canvas.py
import cv2
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from canvas.drawing_engine import DrawingEngine
from tools.tool_types import ToolType
from tools.curve_tools import CurveTool, PolyCurveTool
from tools.line_tools import  LineTool, PolylineTool

class ImageCanvas(QLabel):
    def __init__(self):
        super().__init__()
        self.cv_img = None
        self.zoom = 1.0

        # YOLO data
        self.boxes = []
        self.hover_box = None

        # Drawing
        self.drawing_enabled = False
        self.drawing_engine = None

        # callbacks
        self.click_callback = None
        self.move_callback = None
        self.release_callback = None
        self.log_callback = None

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Tools
        self.curve_tool = CurveTool(log_callback=self.log_callback)
        self.polycurve_tool = PolyCurveTool(log_callback=self.log_callback)
        self.line_tool = LineTool(log_callback=self.log_callback)
        self.polyline_tool = PolylineTool(log_callback=self.log_callback)

    # ------------------------- Image -------------------------
    def set_image(self, cv_img):
        self.cv_img = cv_img
        self.drawing_engine = DrawingEngine(cv_img=self.cv_img, log_callback=self.log_callback)
        self.redraw()

    def redraw(self):
        if self.cv_img is None:
            return

        h, w = self.cv_img.shape[:2]
        img = cv2.resize(self.cv_img, (int(w * self.zoom), int(h * self.zoom)))

        # YOLO boxes
        for i, (x1, y1, x2, y2, cls) in enumerate(self.boxes):
            zx1, zy1 = int(x1 * self.zoom), int(y1 * self.zoom)
            zx2, zy2 = int(x2 * self.zoom), int(y2 * self.zoom)
            color = (0, 255, 0) if cls == 1 else (0, 0, 255)
            if self.hover_box == i:
                color = (255, 0, 0)
            cv2.rectangle(img, (zx1, zy1), (zx2, zy2), color, 2)

        # Tool previews
        dl = self.drawing_engine
        if dl:
            if dl.tool == ToolType.POLYLINE:
                self.polyline_tool.draw(img, zoom=self.zoom, preview=True)
            elif dl.tool == ToolType.CURVE:
                self.curve_tool.draw(img, zoom=self.zoom, preview=True)
            elif dl.tool == ToolType.POLYCURVE:
                self.polycurve_tool.draw(img, zoom=self.zoom, preview=True)
            elif dl.tool == ToolType.LINE:
                self.line_tool.draw(img, zoom=self.zoom)
            elif dl.tool in [ToolType.FREEHAND, ToolType.WHITE]:
                dl.draw_preview(img, zoom=self.zoom)  # stará logika alebo neskôr migrovať

        # Convert to QImage a nastav pixmap
        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_img = QImage(img.data.tobytes(), w, h, bytes_per_line, QImage.Format.Format_BGR888)
        self.setPixmap(QPixmap.fromImage(q_img))
        self.setFixedSize(w, h)

    # ------------------------- Mouse Events -------------------------
    def mousePressEvent(self, event):
        self.setFocus()
        x, y = int(event.position().x() / self.zoom), int(event.position().y() / self.zoom)
        dl = self.drawing_engine

        # Undo pravým tlačidlom pre polyline/curve/polycurve
        if event.button() == Qt.MouseButton.RightButton:
            if dl and dl.tool in [ToolType.POLYLINE, ToolType.CURVE, ToolType.POLYCURVE]:
                if dl.tool == ToolType.POLYLINE:
                    self.polyline_tool.undo_last_point()
                elif dl.tool == ToolType.CURVE:
                    self.curve_tool.undo_last_point()
                elif dl.tool == ToolType.POLYCURVE:
                    self.polycurve_tool.undo_last_point()
                self.redraw()
            return

        # ----------- Bodové nástroje -----------
        if dl and dl.tool in [ToolType.LINE, ToolType.POLYLINE, ToolType.CURVE, ToolType.POLYCURVE]:
            if dl.tool == ToolType.LINE:
                line = self.line_tool
                if not line.points:
                    line.start_point_line(x, y)
                elif len(line.points) == 1:
                    line.add_point_line(x, y)
                    line.finalize(self.cv_img)
                self.redraw()
                return
            elif dl.tool == ToolType.POLYLINE:
                if not self.polyline_tool.points:
                    self.polyline_tool.start_point(x, y)
                else:
                    self.polyline_tool.add_point(x, y)
                self.redraw()
                return
            elif dl.tool == ToolType.CURVE:
                if not self.curve_tool.points:
                    self.curve_tool.start_point(x, y)
                else:
                    self.curve_tool.add_point(x, y)
                self.redraw()
                return
            elif dl.tool == ToolType.POLYCURVE:
                if not self.polycurve_tool.points:
                    self.polycurve_tool.start_point(x, y)
                else:
                    self.polycurve_tool.add_point(x, y)
                self.redraw()
                return

        # ----------- Staré drawing tools (FREEHAND, WHITE, LINE pre dl.tool) -----------
        if self.drawing_enabled and dl:
            dl.start_draw(x, y)
            return

        # ----------- YOLO delete -----------
        self.click_callback and self.click_callback(event)

    def mouseMoveEvent(self, event):
        x, y = int(event.position().x() / self.zoom), int(event.position().y() / self.zoom)
        dl = self.drawing_engine

        # ----------- Preview pre bodové nástroje -----------
        if dl and dl.tool in [ToolType.LINE, ToolType.POLYLINE, ToolType.CURVE, ToolType.POLYCURVE]:
            if dl.tool == ToolType.LINE:
                # preview bod pred prvým klikom
                if not self.line_tool.points:
                    self.line_tool.preview_point = (x, y)
                else:
                    self.line_tool.set_preview(x, y)
            elif dl.tool == ToolType.POLYLINE:
                self.polyline_tool.set_preview(x, y)
            elif dl.tool == ToolType.CURVE:
                self.curve_tool.set_preview(x, y)
            elif dl.tool == ToolType.POLYCURVE:
                self.polycurve_tool.set_preview(x, y)

            self.redraw()
            return

        # ----------- Drawing pre FREEHAND / WHITE / LINE -----------
        if self.drawing_enabled and dl and dl.drawing:
            dl.move_draw(x, y)
            self.redraw()
            return

        # ----------- YOLO hover -----------
        self.move_callback and self.move_callback(event)
    def mouseReleaseEvent(self, event):
        x, y = int(event.position().x() / self.zoom), int(event.position().y() / self.zoom)
        dl = self.drawing_engine
        if self.drawing_enabled and dl and dl.drawing:
            dl.end_draw(x, y)
            self.log_callback and self.log_callback("Drawing ended")
            self.redraw()
        self.release_callback and self.release_callback(event)

    # ------------------------- Key Events -------------------------
    def keyPressEvent(self, event):
        dl = self.drawing_engine
        if not dl or dl.tool not in [ToolType.POLYLINE, ToolType.CURVE, ToolType.POLYCURVE]:
            return super().keyPressEvent(event)

        key = event.key()
        # FINALIZE
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if dl.tool == ToolType.POLYLINE:
                self.polyline_tool.finalize(self.cv_img)
                dl._log("Polyline finalized")
            elif dl.tool == ToolType.CURVE:
                self.curve_tool.finalize(self.cv_img)
                dl._log("Curve finalized")
            elif dl.tool == ToolType.POLYCURVE:
                self.polycurve_tool.finalize(self.cv_img)
                dl._log("PolyCurve finalized")
            self.redraw()

        # CANCEL
        elif key == Qt.Key.Key_Escape:
            if dl.tool == ToolType.POLYLINE:
                self.polyline_tool.points.clear()
                self.polyline_tool.preview_point = None
                dl._log("Polyline cancelled")
            elif dl.tool == ToolType.CURVE:
                self.curve_tool.points.clear()
                self.curve_tool.preview_point = None
                dl._log("Curve cancelled")
            elif dl.tool == ToolType.POLYCURVE:
                self.polycurve_tool.points.clear()
                self.polycurve_tool.preview_point = None
                dl._log("PolyCurve cancelled")
            self.redraw()