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
    """Vracia cestu k zdroju, funguje lokálne aj v EXE."""
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
        self.yolo_auto = False

        # IMAGE
        self.cv_image = None
        self.boxes = []
        self.deleted_boxes = []
        self.hover_box = None
        self.zoom = 1.0

        # TOOLS
        self.current_tool_type = None
        self.brush_size = 1
        self.brush_color = (0, 0, 0)
        self.shortcuts = []
        self.tool_buttons = {}

        # FOLDER
        self.image_paths = []
        self.current_index = 0
        self.last_folder = ""

        # WIDGETS
        self.load_btn = QPushButton()
        self.prev_btn = QPushButton()
        self.next_btn = QPushButton()
        self.process_btn = QPushButton()  # YOLO / YOLO Auto
        self.save_btn = QPushButton()
        self.log_btn = QPushButton()

        self.freehand_btn = QPushButton()
        self.line_btn = QPushButton()
        self.polyline_btn = QPushButton()
        self.curve_btn = QPushButton()
        self.polycurve_btn = QPushButton()
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
    # ------------------------- BUILD GUI -------------------------
    def build_gui(self):
        self.image_label = ImageCanvas()
        self.image_label.log_callback = self.log_msg
        self.image_label.click_callback = self.on_click
        self.image_label.move_callback = self.on_mouse_move
        self.image_label.release_callback = self.on_mouse_release

        # label pre zobrazenie cesty k súboru
        self.path_label = QLabel()
        self.path_label.setStyleSheet("font-weight: bold;")
        self.path_label.setWordWrap(True)

        scroll = self.create_scroll_area(self.image_label)

        # nový wrapper widget pre label + scroll
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

            # priradenie YOLO a LOG buttonov
            if tool_enum == MainToolbar.YOLO:
                self.process_btn = btn
            if tool_enum == MainToolbar.LOG:
                self.log_btn = btn

            icon_file = str(resource_path(ICON_PATH + props["icon"]))
            btn.setIcon(QIcon(icon_file))
            btn.setIconSize(QSize(64, 64))
            btn.setToolTip(props["tooltip"])
            btn.setFixedSize(80, 80)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # odpojenie starých signálov
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
        self.tool_buttons = {
            ToolType.FREEHAND: self.freehand_btn,
            ToolType.LINE: self.line_btn,
            ToolType.POLYLINE: self.polyline_btn,
            ToolType.CURVE: self.curve_btn,
            ToolType.POLYCURVE: self.polycurve_btn,
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
            btn.setToolTip(f'{props["tooltip"]} ({props["shortcut"]})')
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

            # pripoj callback len raz
            try:
                btn.clicked.disconnect()
            except TypeError:
                pass
            btn.clicked.connect(lambda checked=False, t=tool_enum: self.select_tool(t))

            shortcut = QShortcut(QKeySequence(props["shortcut"]), self)
            shortcut.activated.connect(lambda t=tool_enum: self.select_tool(t))
            self.shortcuts.append(shortcut)

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
        self.brush_slider.valueChanged.connect(self.update_brush_size)

    # ------------------------- LOG -------------------------
    def log_msg(self, msg):
        print(msg)
        self.log.append(msg)

    # ------------------------- TOGGLE LOG PANEL -------------------------
    def toggle_log(self):
        idx = self.image_log_splitter.indexOf(self.log)
        sizes = self.image_log_splitter.sizes()
        if sizes[idx] == 0:
            sizes[idx] = 120
            self.log.setVisible(True)
            if not getattr(self, "_log_visible_last", None):
                self.log_msg("Log panel shown")
                self._log_visible_last = True
        else:
            sizes[idx] = 0
            self.log.setVisible(False)
            if getattr(self, "_log_visible_last", None) != False:
                self.log_msg("Log panel hidden")
                self._log_visible_last = False
        self.image_log_splitter.setSizes(sizes)

    # ------------------------- YOLO -------------------------
    def toggle_yolo_auto(self):
        self.yolo_auto = not self.yolo_auto
        btn = self.process_btn
        if self.yolo_auto:
            btn.setIcon(QIcon(str(resource_path(ICON_PATH + "yolo_auto.png"))))
            self.log_msg("YOLO Auto ON")
            if self.cv_image is not None:
                self._run_yolo_with_loading()  # <-- overlay loading screen
        else:
            btn.setIcon(QIcon(str(resource_path(ICON_PATH + "yolo.png"))))
            self.log_msg("YOLO Auto OFF")

    def _run_yolo_with_loading(self):
        """Spustí YOLO detekciu a zobrazí loading overlay počas spracovania."""
        loading_label = QLabel("YOLO is running...", self)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("background-color: rgba(0,0,0,0.6); color: white; font-size: 24px;")
        loading_label.resize(self.width(), self.height())
        loading_label.show()
        QApplication.processEvents()

        # spustenie detekcie synchronne
        self.process_image()

        # skryť overlay
        loading_label.hide()
        loading_label.deleteLater()

    # ------------------------- SAVE IMAGE -------------------------
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

    # ------------------------- FIT ZOOM -------------------------
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

        # zrušenie aktuálneho nástroja, ak klikneme na ten istý
        if self.current_tool_type == tool_enum:
            self.current_tool_type = None
            self.image_label.drawing_enabled = False
            dl.tool = None
            self._highlight_button(None)
            self.log_msg("No tool active")
            return

        self.current_tool_type = tool_enum
        self.image_label.drawing_enabled = True

        # --------- klasické kreslenie ---------
        if tool_enum in [ToolType.FREEHAND, ToolType.LINE, ToolType.WHITE, ToolType.TEXT, ToolType.UNDO]:
            dl.tool = tool_enum
            dl.brush_size = self.brush_size
            dl.brush_color = (255, 255, 255) if tool_enum == ToolType.WHITE else (0, 0, 0)

        # --------- PolyLine ---------
        elif tool_enum == ToolType.POLYLINE:
            dl.tool = tool_enum
            polyline = self.image_label.polyline_tool
            polyline.points.clear()
            polyline.preview_point = None
            polyline.log_callback = self.image_label.log_callback

        # --------- Curve ---------
        elif tool_enum == ToolType.CURVE:
            dl.tool = tool_enum
            curve = self.image_label.curve_tool
            curve.points.clear()
            curve.preview_point = None
            curve.log_callback = self.image_label.log_callback

        # --------- PolyCurve ---------
        elif tool_enum == ToolType.POLYCURVE:
            dl.tool = tool_enum
            polycurve = self.image_label.polycurve_tool
            polycurve.points.clear()
            polycurve.preview_point = None
            polycurve.log_callback = self.image_label.log_callback

        # zvýraznenie tlačidla
        self._highlight_button(tool_enum)
        self.log_msg(f"Selected tool: {tool_enum.name}")

    def _highlight_button(self, tool_enum):
        for t, btn in self.tool_buttons.items():
            if t == tool_enum:
                btn.setStyleSheet("background-color: lightblue;")
            else:
                btn.setStyleSheet("")

    def update_brush_size(self, value):
        self.brush_size = value
        self.brush_label.setText(f"Brush: {value}")

        dl = self.image_label.drawing_engine
        if dl:
            dl.brush_size = value  # pre FREEHAND / WHITE / LINE stará logika

        # Nová logika pre nové nástroje
        self.image_label.line_tool.brush_size = value
        self.image_label.polyline_tool.brush_size = value
        self.image_label.curve_tool.brush_size = value
        self.image_label.polycurve_tool.brush_size = value

        self.log_msg(f"Brush size set to {value}")

    # ------------------------- LOAD / NAVIGATION -------------------------
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

    # ------------------------- MOUSE -------------------------
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

    # ------------------------- ZOOM -------------------------
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
    print(f"Loaded YOLO model from: {model_path}")

    window = MainWindow(yolo)
    window.show()
    sys.exit(app.exec())