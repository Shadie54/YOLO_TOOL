import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
import cv2
import ctypes
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QTextEdit, QFileDialog, QSlider, QLabel, QSizePolicy
)
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QSize
from canvas.image_canvas import ImageCanvas
from yolo.yolo_processor import YoloProcessor
from tools.delete_tools import DeleteTool
from tools.tool_registry import TOOL_REGISTRY
from tools.tool_types import ToolType
from pathlib import Path

# ------------------------- RESOURCE PATH -------------------------
def resource_path(relative_path: str) -> str:
    """Vracia cestu k zdroju, funguje lokálne aj v EXE."""
    try:
        # PyInstaller onedir/onefile
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
class MainWindow(QWidget):

    def __init__(self, yolo_processor):
        self.yolo = yolo_processor
        super().__init__()
        self.setWindowTitle("YoloCAT - interaktívny nástroj na miestopisy")
        self.resize(1400, 1000)
        self.setWindowIcon(QIcon(resource_path("assets/icons/yolocat.ico")))
        # ------------------------- MODEL -------------------------
        self.yolo = yolo
        self.yolo_auto = False

        # ------------------------- IMAGE -------------------------
        self.cv_image = None
        self.boxes = []
        self.deleted_boxes = []
        self.hover_box = None
        self.zoom = 1.0
        # ---------------------- TOOL BUTTONS ----------------------
        self.tool_buttons = {}
        # ------------------------- TOOLS -------------------------
        self.current_tool_type = None
        self.brush_size = 1
        self.brush_color = (0, 0, 0)

        # ------------------------- FOLDER -------------------------
        self.image_paths = []
        self.current_index = 0
        self.last_folder = ""

        # ------------------------- WIDGETS -------------------------
        self.load_btn = QPushButton()
        self.prev_btn = QPushButton()
        self.next_btn = QPushButton()
        self.process_btn = QPushButton()  # YOLO / YOLO Auto
        self.save_btn = QPushButton()
        self.freehand_btn = QPushButton()
        self.line_btn = QPushButton()
        self.white_btn = QPushButton()
        self.text_btn = QPushButton()
        self.undo_btn = QPushButton()
        self.brush_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_label = QLabel()
        self.log = QTextEdit()
        self.image_label = None
        self.delete_tool = None

        self.build_gui()

    # ------------------------- BUILD GUI -------------------------
    def build_gui(self):
        self.image_label = ImageCanvas()
        self.image_label.log_callback = self.log_msg
        self.image_label.click_callback = self.on_click
        self.image_label.move_callback = self.on_mouse_move
        self.image_label.release_callback = self.on_mouse_release

        scroll = self.create_scroll_area(self.image_label)
        toolbar_layout = self.create_toolbar()

        self.create_tools()  # <--- nastaví tlačidlá tool_buttons
        tool_panel_layout = self.create_tool_panel()  # teraz tlačidlá + brush slider

        log_widget = self.create_log_panel()

        top_layout = QHBoxLayout()
        top_layout.addLayout(toolbar_layout)
        top_layout.addWidget(scroll)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(tool_panel_layout)
        main_layout.addWidget(log_widget)
        self.setLayout(main_layout)

        self.connect_signals()
        self.delete_tool = DeleteTool(self.image_label)

    # ------------------------- SCROLL AREA -------------------------
    @staticmethod
    def create_scroll_area(widget):
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        return scroll

    # ------------------------- TOOLBAR -------------------------
    def create_toolbar(self):
        buttons = [self.load_btn, self.prev_btn, self.next_btn, self.process_btn, self.save_btn]
        icons = ["open.png", "left.png", "right.png", "yolo.png", "save.png"]
        icon_path = "assets/icons/"

        for b, icon_file in zip(buttons, icons):
            b.setMaximumSize(100, 100)
            b.setMinimumSize(50, 50)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            b.setIcon(QIcon(resource_path(os.path.join(icon_path, icon_file))))
            b.setIconSize(QSize(64, 64))
            b.setText("")

        layout = QVBoxLayout()
        for b in buttons:
            layout.addWidget(b)
        layout.addStretch()
        return layout

    # ----------------- create_tools -----------------
    def create_tools(self):
        # tlačidlá z __init__
        self.tool_buttons = {
            ToolType.FREEHAND: self.freehand_btn,
            ToolType.LINE: self.line_btn,
            ToolType.WHITE: self.white_btn,
            ToolType.TEXT: self.text_btn,
            ToolType.UNDO: self.undo_btn
        }

        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 0, 0, 0)

        for tool_enum, btn in self.tool_buttons.items():
            props = TOOL_REGISTRY[tool_enum]
            btn.setIcon(QIcon(resource_path(props["icon"])))
            btn.setIconSize(QSize(64, 64))
            btn.setFixedSize(80, 80)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            btn.clicked.connect(lambda checked=False, t=tool_enum: self.select_tool(t))
            shortcut = QShortcut(QKeySequence(props["shortcut"]), self)
            shortcut.activated.connect(lambda t=tool_enum: self.select_tool(t))

            layout.addWidget(btn)

        layout.addStretch()
        return layout

    # ------------------------- TOOL PANEL -------------------------
    def create_tool_panel(self):
        self.brush_label.setText(f"Brush: {self.brush_size}")
        self.brush_slider.setMinimum(1)
        self.brush_slider.setMaximum(10)
        self.brush_slider.setValue(self.brush_size)
        self.brush_slider.setFixedWidth(150)

        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 0, 0, 0)

        for btn in self.tool_buttons.values():
            layout.addWidget(btn)

        layout.addWidget(self.brush_label)
        layout.addWidget(self.brush_slider)
        layout.addStretch()
        return layout
    # ------------------------- LOG PANEL -------------------------
    def create_log_panel(self):
        self.log.setMaximumHeight(120)
        self.log.setReadOnly(True)
        return self.log

    # ------------------------- SIGNALS -------------------------
    def connect_signals(self):
        self.load_btn.clicked.connect(self.load_folder)
        self.prev_btn.clicked.connect(self.prev_image)
        self.next_btn.clicked.connect(self.next_image)
        self.process_btn.clicked.connect(self.toggle_yolo_auto)
        self.save_btn.clicked.connect(self.save_image)
        self.brush_slider.valueChanged.connect(self.update_brush_size)

    # ------------------------- LOG -------------------------
    def log_msg(self, msg):
        print(msg)
        self.log.append(msg)

    # ------------------------- YOLO AUTO -------------------------
    def toggle_yolo_auto(self):
        self.yolo_auto = not self.yolo_auto
        if self.yolo_auto:
            self.process_btn.setIcon(QIcon(resource_path("assets/icons/yolo_auto.png")))
            self.log_msg("YOLO Auto ON")
            if self.cv_image is not None:
                self._run_yolo_with_loading()
        else:
            self.process_btn.setIcon(QIcon(resource_path("assets/icons/yolo.png")))
            self.log_msg("YOLO Auto OFF")

    def _run_yolo_with_loading(self):
        """Spustí YOLO detekciu a zobrazí loading overlay počas spracovania."""
        loading_label = QLabel("YOLO is running...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("background-color: rgba(0,0,0,0.6); color: white; font-size: 24px;")
        loading_label.setParent(self)
        loading_label.resize(self.width(), self.height())
        loading_label.show()
        QApplication.processEvents()

        # --------- spustenie detekcie synchronne ----------
        self.process_image()

        # --------- skryť loading ----------
        loading_label.hide()
        loading_label.deleteLater()

    # ------------------------- YOLO PROCESS -------------------------
    def process_image(self):
        if self.cv_image is None:
            return

        self.log_msg("Running YOLO...")
        results = self.yolo.model(self.cv_image)[0]

        self.boxes = []
        for i, box in enumerate(results.boxes.xyxy.cpu().numpy()):
            cls = int(results.boxes.cls[i].cpu().numpy())
            x1, y1, x2, y2 = map(int, box)
            if cls == 1:
                x2 = int(x1 + (x2 - x1) * 2.5)
            self.boxes.append((x1, y1, x2, y2, cls))

        self.redraw()
        self.log_msg(f"Detections: {len(self.boxes)}")

    # ------------------------- REDRAW -------------------------
    def redraw(self):
        self.image_label.boxes = self.boxes
        self.image_label.deleted_boxes = self.deleted_boxes
        self.image_label.hover_box = self.hover_box
        self.image_label.zoom = self.zoom
        self.image_label.redraw()

    # ------------------------- SELECT TOOL -------------------------
    def select_tool(self, tool_enum: ToolType):
        dl = self.image_label.drawing_engine
        if not dl:
            return

        # Toggle tool
        if self.current_tool_type == tool_enum:
            self.current_tool_type = None
            self.image_label.drawing_enabled = False
            dl.tool = None
            self._highlight_button(None)  # zruší highlight
            # logujeme len keď sa zmení stav
            self.log_msg("No tool active")
            return

        self.current_tool_type = tool_enum
        self.image_label.drawing_enabled = True
        dl.tool = tool_enum
        dl.brush_size = self.brush_size
        dl.brush_color = (255, 255, 255) if tool_enum == ToolType.WHITE else (0, 0, 0)

        self._highlight_button(tool_enum)
        self.log_msg(f"Selected tool: {tool_enum.name}")

    # ------------------------- RESET BUTTONS -------------------------
    def _reset_tool_buttons(self):
        for btn in self.tool_buttons.values():
            btn.setStyleSheet("")

    # ------------------------- HIGHLIGHT BUTTON -------------------------
    def _highlight_button(self, tool_enum):
        for t, btn in self.tool_buttons.items():
            if t == tool_enum:
                btn.setStyleSheet("background-color: lightblue;")
            else:
                btn.setStyleSheet("")

    # ------------------------- BRUSH -------------------------
    def update_brush_size(self, value):
        self.brush_size = value
        self.brush_label.setText(f"Brush: {value}")
        if self.image_label.drawing_engine:
            self.image_label.drawing_engine.brush_size = value
        self.log_msg(f"Brush size set to {value}")

    # ------------------------- LOAD / NAVIGATION -------------------------


    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.last_folder or "")
        if not folder:
            return

        # absolutna cesta a Path objekt pre správne diakritiku
        folder_path = Path(folder).resolve()
        self.last_folder = str(folder_path)

        # načítanie obrázkov
        self.image_paths = [
            str(folder_path / f) for f in sorted(os.listdir(folder_path))
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        if not self.image_paths:
            self.log_msg("No images found")
            return

        self.current_index = 0
        self.load_image()

    def load_image(self):
        path = self.image_paths[self.current_index]
        try:
            data = np.frombuffer(open(path, "rb").read(), np.uint8)
            self.cv_image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception as e:
            self.log_msg(f"Failed loading image: {path}")
            self.log_msg(f"Failed loading image: {e}")
            return

        self.boxes = []
        self.deleted_boxes = []
        self.hover_box = None
        self.fit_zoom()
        self.image_label.set_image(self.cv_image)

        if self.yolo_auto:
            self.process_image()
        else:
            self.redraw()

        self.log_msg(f"Loaded: {path}")

    def prev_image(self):
        if not self.image_paths: return
        self.current_index = max(0, self.current_index - 1)
        self.load_image()

    def next_image(self):
        if not self.image_paths: return
        self.current_index = min(len(self.image_paths) - 1, self.current_index + 1)
        self.load_image()

    # ------------------------- MOUSE EVENTS -------------------------
    def on_click(self, event):
        if self.cv_image is None or not self.boxes: return
        x = int(event.position().x() / self.zoom)
        y = int(event.position().y() / self.zoom)
        deleted = self.delete_tool.click(x, y, self.boxes)
        if deleted:
            x1, y1, x2, y2, _ = deleted
            cv2.rectangle(self.cv_image, (x1, y1), (x2, y2), (255, 255, 255), -1)
            self.deleted_boxes.append(deleted)
            self.redraw()
            self.log_msg(f"Deleted YOLO box: {deleted[:4]}")

    def on_mouse_move(self, event):
        if self.cv_image is None or not self.boxes: return
        x = int(event.position().x() / self.zoom)
        y = int(event.position().y() / self.zoom)
        new_hover = self.delete_tool.hover(x, y, self.boxes)
        if new_hover != self.hover_box:
            self.hover_box = new_hover
            self.redraw()

    def on_mouse_release(self, event):
        pass

    # ------------------------- SAVE -------------------------
    def save_image(self):
        if self.cv_image is None: return
        folder = os.path.dirname(self.image_paths[self.current_index])
        out_folder = os.path.join(folder, "output")
        os.makedirs(out_folder, exist_ok=True)
        filename = os.path.basename(self.image_paths[self.current_index])
        save_path = os.path.join(out_folder, filename)
        cv2.imwrite(save_path, self.cv_image)
        self.log_msg(f"Saved: {save_path}")

    # ------------------------- ZOOM -------------------------
    def wheelEvent(self, event):
        if self.cv_image is None: return
        delta = event.angleDelta().y()
        self.zoom *= 1.15 if delta > 0 else 0.87
        self.zoom = max(0.2, min(self.zoom, 5))
        self.redraw()

    # ------------------------- FIT / RESIZE -------------------------
    def fit_zoom(self):
        if self.cv_image is None: return
        img_h, img_w = self.cv_image.shape[:2]
        view_w = self.image_label.parent().width()
        view_h = self.image_label.parent().height()
        self.zoom = min(view_w / img_w, view_h / img_h)

    # ----------------- resize event -----------------
    def resizeEvent(self, event):
        self.fit_zoom()
        self.redraw()
        super().resizeEvent(event)

# ------------------------- MAIN -------------------------
if __name__ == "__main__":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("YoloCAT")
    app = QApplication(sys.argv)

    # ---------- Load YOLO model ----------
    model_path = resource_path("models/best.pt")
    yolo = YoloProcessor(model_path)
    yolo.load_model()
    print(f"Loaded YOLO model from: {model_path}")

    # ---------- Start main window ----------
    window = MainWindow(yolo)
    window.show()
    sys.exit(app.exec())