import cv2
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from canvas.drawing_engine import DrawingEngine
from tools.tool_types import ToolType
from tools.curve_tools import CurveTool, PolyCurveTool

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

        self.curve_tool = CurveTool(log_callback=self.log_callback)
        self.polycurve_tool = PolyCurveTool(log_callback=self.log_callback)

    # ------------------------- Image -------------------------
    def set_image(self, cv_img):
        self.cv_img = cv_img
        self.drawing_engine = DrawingEngine(cv_img=self.cv_img, log_callback=self.log_callback)
        self.redraw()

    def redraw(self):
        if self.cv_img is None:
            return
        h, w = self.cv_img.shape[:2]
        new_w = int(w * self.zoom)
        new_h = int(h * self.zoom)
        img = cv2.resize(self.cv_img, (new_w, new_h))

        # YOLO boxes
        for i, (x1, y1, x2, y2, cls) in enumerate(self.boxes):
            zx1 = int(x1 * self.zoom)
            zy1 = int(y1 * self.zoom)
            zx2 = int(x2 * self.zoom)
            zy2 = int(y2 * self.zoom)
            color = (0, 255, 0) if cls == 1 else (0, 0, 255)
            if self.hover_box == i:
                color = (255, 0, 0)
            cv2.rectangle(img, (zx1, zy1), (zx2, zy2), color, 2)

        # ----------------- Curve / PolyCurve preview -----------------

        # Curve preview
        if self.drawing_engine and self.drawing_engine.tool == ToolType.CURVE:
            self.curve_tool.draw(img, zoom=self.zoom, preview=True)

        # PolyCurve preview
        if self.drawing_engine and self.drawing_engine.tool == ToolType.POLYCURVE:
            self.polycurve_tool.draw(img, zoom=self.zoom, preview=True)

        # Line preview
        dl = self.drawing_engine
        if dl and dl.tool == ToolType.LINE and dl.preview_line:
            (x1, y1), (x2, y2) = dl.preview_line
            cv2.line(
                img,
                (int(x1*self.zoom), int(y1*self.zoom)),
                (int(x2*self.zoom), int(y2*self.zoom)),
                dl.brush_color,
                dl.brush_size,
                cv2.LINE_8
            )

        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_img = QImage(img.data.tobytes(), w, h, bytes_per_line, QImage.Format.Format_BGR888)
        self.setPixmap(QPixmap.fromImage(q_img))
        self.setFixedSize(w, h)

    # ------------------------- Mouse -------------------------
    def mousePressEvent(self, event):
        self.setFocus()
        x = int(event.position().x() / self.zoom)
        y = int(event.position().y() / self.zoom)

        if event.button() == Qt.MouseButton.RightButton:

            if self.drawing_engine and self.drawing_engine.tool == ToolType.CURVE:
                self.curve_tool.undo_last_point()
                self.redraw()
                return

            if self.drawing_engine and self.drawing_engine.tool == ToolType.POLYCURVE:
                self.polycurve_tool.undo_last_point()
                self.redraw()
                return

        # ----- CURVE -----
        if self.drawing_engine and self.drawing_engine.tool == ToolType.CURVE:
            if not self.curve_tool.points:
                self.curve_tool.start_point(x, y)
            else:
                self.curve_tool.add_point(x, y)
            self.redraw()
            return

        # ----- POLYCURVE -----
        if self.drawing_engine and self.drawing_engine.tool == ToolType.POLYCURVE:
            if not self.polycurve_tool.points:
                self.polycurve_tool.start_point(x, y)
            else:
                self.polycurve_tool.add_point(x, y)
            self.redraw()
            return

        # ----- OTHER DRAW TOOLS (freehand / line / white) -----
        if self.drawing_enabled and self.drawing_engine:
            self.log_callback and self.log_callback("Drawing started")
            self.drawing_engine.start_draw(x, y)
            return

        # ----- YOLO DELETE TOOL -----
        self.click_callback and self.click_callback(event)

    def mouseMoveEvent(self, event):
        x = int(event.position().x() / self.zoom)
        y = int(event.position().y() / self.zoom)
        if self.drawing_enabled and self.drawing_engine and self.drawing_engine.drawing:
            self.drawing_engine.move_draw(x, y)
            self.redraw()
            return

        if self.drawing_enabled and self.drawing_engine and self.drawing_engine.tool in [ToolType.CURVE, ToolType.POLYCURVE]:
            if self.drawing_engine.tool == ToolType.CURVE:
                self.curve_tool.set_preview(x, y)

            elif self.drawing_engine.tool == ToolType.POLYCURVE:
                self.polycurve_tool.set_preview(x, y)

            self.redraw()

        self.move_callback and self.move_callback(event)

    def mouseReleaseEvent(self, event):
        x = int(event.position().x() / self.zoom)
        y = int(event.position().y() / self.zoom)
        if self.drawing_enabled and self.drawing_engine and self.drawing_engine.drawing:
            self.drawing_engine.end_draw(x, y)
            self.log_callback and self.log_callback("Drawing ended")
            self.redraw()
        self.release_callback and self.release_callback(event)

    def keyPressEvent(self, event):
        if not self.drawing_engine or self.drawing_engine.tool not in [ToolType.CURVE, ToolType.POLYCURVE]:
            return super().keyPressEvent(event)

        dl = self.drawing_engine
        key = event.key()

        # ---------------- FINALIZE ----------------
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):

            if dl.tool == ToolType.CURVE:
                self.curve_tool.finalize(self.cv_img)
                dl._log("Curve finalized")

            elif dl.tool == ToolType.POLYCURVE:
                self.polycurve_tool.finalize(self.cv_img)
                dl._log("PolyCurve finalized")

            self.redraw()

        # ---------------- CANCEL ----------------
        elif key == Qt.Key.Key_Escape:

            if dl.tool == ToolType.CURVE:
                self.curve_tool.points.clear()
                dl._log("Curve cancelled")

            elif dl.tool == ToolType.POLYCURVE:
                self.polycurve_tool.points.clear()
                dl._log("PolyCurve cancelled")

            self.redraw()
