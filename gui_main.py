# gui_main.py
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
import cv2
import ctypes
import numpy as np
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QTextEdit, QFileDialog, QSlider, QLabel, QSizePolicy, QSplitter
)
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QSize

from canvas.image_canvas import ImageCanvas
from yolo.yolo_processor import YoloProcessor
from tools.delete_tools import DeleteTool
from tools.tool_registry import MAIN_TOOLBAR_REGISTRY, TOOL_REGISTRY, MainToolbar, ICON_PATH
from tools.tool_types import ToolType

# ------------------------- RESOURCE PATH -------------------------
def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ------------------------- MAIN WINDOW -------------------------
class MainWindow(QWidget):
    def __init__(self, yolo_processor):
        super().__init__()
        self.setWindowTitle("YoloCAT v1.0 - interaktívny nástroj na miestopisy")
        self.resize(1400, 1000)
        self.setWindowIcon(QIcon(resource_path("assets/icons/yolocat.ico")))

        # YOLO
        self.yolo = yolo_processor

        # IMAGE
        self.cv_image = None
        self.boxes = []
        self.deleted_boxes = []
        self.hover_box = None
        self.zoom = 1.0

        # TOOLS
        self.current_tool_type = None
        self.brush_size = 1
        self.tool_buttons = {}
        self.shortcuts = []

        # FOLDER
        self.image_paths = []
        self.current_index = 0
        self.last_folder = ""

        # WIDGETS
        self.load_btn = QPushButton()
        self.prev_btn = QPushButton()
        self.next_btn = QPushButton()
        self.process_btn = QPushButton()
        self.save_btn = QPushButton()
        self.log_btn = QPushButton()
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

        self.path_label = QLabel()
        self.path_label.setStyleSheet("font-weight: bold;")
        self.path_label.setWordWrap(True)

        scroll = self.create_scroll_area(self.image_label)
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(5)
        scroll_widget = QWidget()
        scroll_widget.setLayout(scroll_layout)
        scroll_layout.addWidget(self.path_label)
        scroll_layout.addWidget(scroll)

        toolbar_layout = self.create_toolbar()
        self.create_tools()
        tool_panel_layout = self.create_tool_panel()
        tools_widget = QWidget()
        tools_widget.setLayout(tool_panel_layout)

        log_widget = self.create_log_panel()

        self.image_log_splitter = QSplitter(Qt.Orientation.Vertical)
        self.image_log_splitter.addWidget(scroll_widget)
        self.image_log_splitter.addWidget(tools_widget)
        self.image_log_splitter.addWidget(log_widget)
        self.image_log_splitter.setSizes([800, 120, 80])
        self.image_log_splitter.setCollapsible(1, False)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.image_log_splitter)

        main_layout = QHBoxLayout()
        main_layout.addLayout(toolbar_layout)
        main_layout.addLayout(right_layout)
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
        layout = QVBoxLayout()
        for tool_enum, props in MAIN_TOOLBAR_REGISTRY.items():
            btn_name = f"{tool_enum.name.lower()}_btn"
            btn = getattr(self, btn_name, None)
            if not btn:
                btn = QPushButton()
                setattr(self, btn_name, btn)

            icon_file = str(resource_path(ICON_PATH + props["icon"]))
            btn.setIcon(QIcon(icon_file))
            btn.setIconSize(QSize(64, 64))
            btn.setToolTip(props["tooltip"])
            btn.setFixedSize(80, 80)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            try:
                btn.clicked.disconnect()
            except TypeError:
                pass
            btn.clicked.connect(getattr(self, props["callback"]))

            layout.addWidget(btn)
        layout.addStretch()
        return layout

    # ------------------------- TOOLS -------------------------
    def create_tools(self):
        layout = QHBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 0, 0, 0)
        for tool_enum, props in TOOL_REGISTRY.items():
            btn = QPushButton()
            btn.setIcon(QIcon(resource_path(props["icon"])))
            btn.setIconSize(QSize(64, 64))
            btn.setFixedSize(80, 80)
            tooltip = props["tooltip"]
            if props["shortcut"]:
                tooltip += f" ({props['shortcut']})"
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked=False, t=tool_enum: self.select_tool(t))
            self.tool_buttons[tool_enum] = btn
            if props["shortcut"]:
                sc = QShortcut(QKeySequence(props["shortcut"]), self)
                sc.activated.connect(lambda t=tool_enum: self.select_tool(t))
                self.shortcuts.append(sc)
            layout.addWidget(btn)
        layout.addStretch()
        return layout

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

    def connect_signals(self):
        self.brush_slider.valueChanged.connect(self.update_brush_size)

    # ------------------------- LOG -------------------------
    def log_msg(self, msg):
        print(msg)
        self.log.append(msg)

    def toggle_log(self):
        idx = self.image_log_splitter.indexOf(self.log)
        sizes = self.image_log_splitter.sizes()
        if sizes[idx] == 0:
            sizes[idx] = 120
            self.log.setVisible(True)
            self.log_msg("Log panel shown")
        else:
            sizes[idx] = 0
            self.log.setVisible(False)
            self.log_msg("Log panel hidden")
        self.image_log_splitter.setSizes(sizes)

    # ------------------------- YOLO -------------------------
    def toggle_yolo_auto(self):
        self.yolo_auto = self.yolo.toggle_auto()
        btn = self.process_btn
        if self.yolo.yolo_auto:
            btn.setIcon(QIcon(resource_path(ICON_PATH + "yolo_auto.png")))
            self.log_msg("YOLO Auto ON")
            if self.cv_image is not None:
                self._run_yolo_with_loading()
        else:
            btn.setIcon(QIcon(resource_path(ICON_PATH + "yolo.png")))
            self.log_msg("YOLO Auto OFF")

    def _run_yolo_with_loading(self):
        loading_label = QLabel("YOLO is running...", self)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("background-color: rgba(0,0,0,0.6); color: white; font-size: 24px;")
        loading_label.resize(self.width(), self.height())
        loading_label.show()
        QApplication.processEvents()
        self.process_image()
        loading_label.hide()
        loading_label.deleteLater()

    # ------------------------- SAVE / LOAD / NAVIGATION -------------------------
    def save_image(self):
        if self.cv_image is None:
            return
        folder = Path(self.image_paths[self.current_index]).parent
        folder_name = folder.name
        out_folder = folder / folder_name
        out_folder.mkdir(exist_ok=True)
        filename = Path(self.image_paths[self.current_index]).name
        save_path = out_folder / filename
        cv2.imwrite(str(save_path), self.cv_image)
        self.log_msg(f"Saved: {save_path}")

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.last_folder or "")
        if not folder: return
        folder_path = Path(folder).resolve()
        self.last_folder = str(folder_path)
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
        self.path_label.setText(path)
        try:
            data = np.frombuffer(open(path, "rb").read(), np.uint8)
            self.cv_image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception as e:
            self.log_msg(f"Failed loading image: {path}")
            self.log_msg(str(e))
            return
        self.boxes = []
        self.deleted_boxes = []
        self.hover_box = None
        self.fit_zoom()
        self.image_label.set_image(self.cv_image)
        if self.yolo.yolo_auto:
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

    # ------------------------- ZOOM / REDRAW -------------------------
    def fit_zoom(self):
        if self.cv_image is None: return
        img_h, img_w = self.cv_image.shape[:2]
        view_w = self.image_label.parent().width()
        view_h = self.image_label.parent().height()
        self.zoom = min(view_w / img_w, view_h / img_h)

    def fit_to_window(self):
        self.fit_zoom()
        self.redraw()
        self.log_msg("Zoom: Fit to window")

    def redraw(self):
        self.image_label.boxes = self.boxes
        self.image_label.deleted_boxes = self.deleted_boxes
        self.image_label.hover_box = self.hover_box
        self.image_label.zoom = self.zoom
        self.image_label.redraw()

    # ------------------------- TOOL SELECTION -------------------------
    def select_tool(self, tool_enum: ToolType):
        if self.current_tool_type == tool_enum:
            self.current_tool_type = None
            self.image_label.drawing_enabled = False
            self.image_label.drawing_engine.tool = None
            self._highlight_button(None)
            self.log_msg("No tool active")
            return
        self.current_tool_type = tool_enum
        self.image_label.drawing_enabled = True
        self.image_label.drawing_engine.tool = tool_enum
        tool = self.image_label.tools.get(tool_enum)
        if tool and hasattr(tool, "points"):
            tool.points.clear()
            tool.preview_point = None
        self._highlight_button(tool_enum)
        self.log_msg(f"Selected tool: {tool_enum.name}")

    def _highlight_button(self, tool_enum):
        for t, btn in self.tool_buttons.items():
            btn.setStyleSheet("background-color: lightblue;" if t == tool_enum else "")

    def update_brush_size(self, value):
        self.brush_size = value
        self.brush_label.setText(f"Brush: {value}")
        for tool in self.image_label.tools.values():
            if hasattr(tool, "brush_size"):
                tool.brush_size = value
        self.image_label.redraw()
        self.log_msg(f"Brush size set to {value}")

    # ------------------------- YOLO DELETE -------------------------
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

    # ------------------------- YOLO PROCESS -------------------------
    def process_image(self):
        if self.cv_image is None: return
        self.boxes = self.yolo.process_with_boxes(self.cv_image)
        self.redraw()
        self.log_msg(f"Detections: {len(self.boxes)}")

    def wheelEvent(self, event):
        if self.cv_image is None: return
        delta = event.angleDelta().y()
        self.zoom *= 1.15 if delta > 0 else 0.87
        self.zoom = max(0.2, min(self.zoom, 5))
        self.redraw()

    def resizeEvent(self, event):
        self.fit_zoom()
        self.redraw()
        super().resizeEvent(event)

# ------------------------- MAIN -------------------------
if __name__ == "__main__":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("YoloCAT")
    app = QApplication(sys.argv)
    model_path = resource_path("models/best.pt")
    yolo = YoloProcessor(model_path)
    yolo.load_model()
    window = MainWindow(yolo)
    window.show()
    sys.exit(app.exec())