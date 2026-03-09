import cv2
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QImage
from canvas.drawing_engine import DrawingEngine

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

        # Line preview
        dl = self.drawing_engine
        if dl and dl.tool == "line" and dl.preview_line:
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
        x = int(event.position().x() / self.zoom)
        y = int(event.position().y() / self.zoom)
        if self.drawing_enabled and self.drawing_engine:
            self.log_callback and self.log_callback("Drawing started")
            self.drawing_engine.start_draw(x, y)
            return
        self.click_callback and self.click_callback(event)

    def mouseMoveEvent(self, event):
        x = int(event.position().x() / self.zoom)
        y = int(event.position().y() / self.zoom)
        if self.drawing_enabled and self.drawing_engine and self.drawing_engine.drawing:
            self.drawing_engine.move_draw(x, y)
            self.redraw()
            return
        self.move_callback and self.move_callback(event)

    def mouseReleaseEvent(self, event):
        x = int(event.position().x() / self.zoom)
        y = int(event.position().y() / self.zoom)
        if self.drawing_enabled and self.drawing_engine and self.drawing_engine.drawing:
            self.drawing_engine.end_draw(x, y)
            self.log_callback and self.log_callback("Drawing ended")
            self.redraw()
        self.release_callback and self.release_callback(event)