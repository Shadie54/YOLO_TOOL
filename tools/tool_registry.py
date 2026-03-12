# tool_registry.py

from enum import Enum, auto
from tools.tool_types import ToolType

ICON_PATH = "assets/icons/"

# ------------------------- DRAW TOOLS -------------------------
TOOL_REGISTRY = {
    ToolType.FREEHAND: {"icon": ICON_PATH + "pencil.png", "tooltip": "Freehand drawing", "shortcut": "F"},
    ToolType.LINE: {"icon": ICON_PATH + "line.png", "tooltip": "Draw line", "shortcut": "L"},
    ToolType.CURVE: {"icon": ICON_PATH + "curve.png", "tooltip": "Draw curve (3 control points)", "shortcut": "C"},
    ToolType.POLYCURVE: {"icon": ICON_PATH + "polycurve.png", "tooltip": "Draw poly-curve (many points)", "shortcut": "P"},
    ToolType.WHITE: {"icon": ICON_PATH + "del.png", "tooltip": "Erase (white brush)", "shortcut": "E"},
    ToolType.TEXT: {"icon": ICON_PATH + "text.png", "tooltip": "Insert text", "shortcut": "T"},
    ToolType.UNDO: {"icon": ICON_PATH + "undo.png", "tooltip": "Undo last action", "shortcut": "Ctrl+Z"},
    ToolType.POLYLINE: {"icon": ICON_PATH + "polyline.png", "tooltip": "Polyline tool", "shortcut": ""},
}

# ------------------------- MAIN TOOLBAR -------------------------
class MainToolbar(Enum):
    OPEN = auto()
    YOLO = auto()
    PREV = auto()
    NEXT = auto()
    SAVE = auto()
    LOG = auto()

MAIN_TOOLBAR_REGISTRY = {
    MainToolbar.OPEN:  {"icon": "open.png", "tooltip": "Open folder (Ctrl+O)", "callback": "load_folder"},
    MainToolbar.YOLO:  {"icon": "yolo.png", "tooltip": "OFF/ON Auto YOLO detection", "callback": "toggle_yolo_auto"},
    MainToolbar.PREV:  {"icon": "left.png", "tooltip": "Previous image", "callback": "prev_image"},
    MainToolbar.NEXT:  {"icon": "right.png", "tooltip": "Next image", "callback": "next_image"},
    MainToolbar.SAVE:  {"icon": "save.png", "tooltip": "Save image (Ctrl+S)", "callback": "save_image"},
    MainToolbar.LOG:   {"icon": "log.png", "tooltip": "Show / Hide log panel", "callback": "toggle_log"},
}