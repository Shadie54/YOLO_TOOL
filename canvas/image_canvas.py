# image_canvas.py
import cv2
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from canvas.drawing_engine import DrawingEngine
from tools.tool_types import ToolType
from tools.curve_tools import CurveTool, PolyCurveTool
from tools.line_tools import LineTool, PolylineTool
from tools.freehand_tools import PencilTool, EraserTool

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

        # Callbacks
        self.click_callback = None
        self.move_callback = None
        self.release_callback = None
        self.log_callback = None

        # Mouse tracking
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.mouse_pressed = False
        self._draw_buffer = []       # body čakajúce na vykreslenie
        self._redraw_interval = 3    # prekresľovanie po N bodoch

        # ------------------------- Tools -------------------------
        self.pencil_tool = PencilTool(log_callback=self.log_callback)
        self.pencil_tool.tool_type = ToolType.PENCIL

        self.eraser_tool = EraserTool(log_callback=self.log_callback)
        self.eraser_tool.tool_type = ToolType.ERASER

        self.line_tool = LineTool(log_callback=self.log_callback)
        self.line_tool.tool_type = ToolType.LINE

        self.polyline_tool = PolylineTool(log_callback=self.log_callback)
        self.polyline_tool.tool_type = ToolType.POLYLINE

        self.curve_tool = CurveTool(log_callback=self.log_callback)
        self.curve_tool.tool_type = ToolType.CURVE

        self.polycurve_tool = PolyCurveTool(log_callback=self.log_callback)
        self.polycurve_tool.tool_type = ToolType.POLYCURVE

        # Dispatcher map
        self.tools = {
            ToolType.PENCIL: self.pencil_tool,
            ToolType.ERASER: self.eraser_tool,
            ToolType.LINE: self.line_tool,
            ToolType.POLYLINE: self.polyline_tool,
            ToolType.CURVE: self.curve_tool,
            ToolType.POLYCURVE: self.polycurve_tool
        }

    # ------------------------- Image -------------------------
    def set_image(self, cv_img):
        self.cv_img = cv_img
        self.drawing_engine = DrawingEngine(cv_img=self.cv_img, log_callback=self.log_callback)
        self.redraw()

    def get_active_tool(self):
        dl = self.drawing_engine
        if not dl:
            return None
        return self.tools.get(dl.tool)

    # ------------------------- Tool preview -------------------------
    def handle_tool_preview(self, x, y):
        tool = self.get_active_tool()
        if not tool:
            return False

        if isinstance(tool, LineTool):
            if not tool.start_point:
                tool.preview_point = (x, y)
            else:
                tool.set_preview(x, y)
        elif hasattr(tool, "set_preview"):
            tool.set_preview(x, y)
        elif hasattr(tool, "points") and not tool.points:
            tool.preview_point = (x, y)
        return True

    # ------------------------- Redraw -------------------------
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
        tool = self.get_active_tool()
        if tool and hasattr(tool, "draw"):
            tool.draw(img, zoom=self.zoom)
        elif self.drawing_engine and self.drawing_engine.tool in [ToolType.PENCIL, ToolType.ERASER]:
            self.drawing_engine.draw_preview(img, zoom=self.zoom)

        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_img = QImage(img.data.tobytes(), w, h, bytes_per_line, QImage.Format.Format_BGR888)
        self.setPixmap(QPixmap.fromImage(q_img))
        self.setFixedSize(w, h)

    # ------------------------- Mouse Press -------------------------
    def mousePressEvent(self, event):
        self.setFocus()
        x, y = int(event.position().x() / self.zoom), int(event.position().y() / self.zoom)
        dl = self.drawing_engine
        self.mouse_pressed = True

        # Right click undo for multi-point tools
        if event.button() == Qt.MouseButton.RightButton:
            if dl and dl.tool in [ToolType.POLYLINE, ToolType.CURVE, ToolType.POLYCURVE]:
                self.tools[dl.tool].undo_last_point()
                self.redraw()
            return

        if dl and dl.tool in self.tools:
            tool = self.tools[dl.tool]
            tool_type = getattr(tool, "tool_type", None)

            # LINE
            if tool_type == ToolType.LINE:
                if not tool.start_point:
                    tool.start_point = (x, y)
                    tool.preview_point = (x, y)
                elif not tool.end_point:
                    tool.end_point = (x, y)
                    tool.preview_point = None
                    tool.finalize(self.cv_img)

            # Pencil / Eraser
            elif tool_type in [ToolType.PENCIL, ToolType.ERASER]:
                tool.add_point(x, y)
                self._draw_buffer.append((x, y))

            # PolyLine / Curve / PolyCurve
            else:
                if not tool.points:
                    tool.start_point(x, y)
                else:
                    tool.add_point(x, y)

            self.redraw()
            return

        # Fallback old drawing tools
        if self.drawing_enabled and dl:
            dl.start_draw(x, y)
            return

        # YOLO delete fallback
        self.click_callback and self.click_callback(event)

    # ------------------------- Mouse Move -------------------------
    def mouseMoveEvent(self, event):
        x, y = int(event.position().x() / self.zoom), int(event.position().y() / self.zoom)
        tool = self.get_active_tool()

        if tool and self.mouse_pressed:
            tool_type = getattr(tool, "tool_type", None)
            if tool_type in [ToolType.PENCIL, ToolType.ERASER]:
                tool.add_point(x, y)
                self._draw_buffer.append((x, y))
                if len(self._draw_buffer) >= self._redraw_interval:
                    self.redraw()
                    self._draw_buffer.clear()
                return

        if self.handle_tool_preview(x, y):
            self.redraw()
            return

        self.move_callback and self.move_callback(event)

    # ------------------------- Mouse Release -------------------------
    def mouseReleaseEvent(self, event):
        x, y = int(event.position().x() / self.zoom), int(event.position().y() / self.zoom)
        self.mouse_pressed = False

        tool = self.get_active_tool()
        tool_type = getattr(tool, "tool_type", None)
        if tool and tool_type in [ToolType.PENCIL, ToolType.ERASER]:
            self._draw_buffer.clear()
            tool.finalize(self.cv_img)
            self.redraw()
            return

        self.release_callback and self.release_callback(event)

    # ------------------------- Key Events -------------------------
    def keyPressEvent(self, event):
        dl = self.drawing_engine
        if not dl or dl.tool not in [ToolType.POLYLINE, ToolType.CURVE, ToolType.POLYCURVE]:
            return super().keyPressEvent(event)

        key = event.key()
        tool = self.tools[dl.tool]

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            tool.finalize(self.cv_img)
            dl._log(f"{dl.tool.name} finalized")
            self.redraw()
        elif key == Qt.Key.Key_Escape:
            tool.points.clear()
            tool.preview_point = None
            dl._log(f"{dl.tool.name} cancelled")
            self.redraw()