from tools.tool_types import FREEHAND, LINE, WHITE, TEXT, UNDO

ICON_PATH = "assets/icons/"

TOOL_REGISTRY = {
    FREEHAND: {
        "icon": ICON_PATH + "pencil.png",
        "tooltip": "Freehand drawing",
        "shortcut": "F",
    },
    LINE: {
        "icon": ICON_PATH + "line.png",
        "tooltip": "Draw line",
        "shortcut": "L",
    },
    WHITE: {
        "icon": ICON_PATH + "del.png",
        "tooltip": "Erase (white brush)",
        "shortcut": "E",
    },
    TEXT: {
        "icon": ICON_PATH + "text.png",
        "tooltip": "Insert text",
        "shortcut": "T",
    },
    UNDO: {
        "icon": ICON_PATH + "undo.png",
        "tooltip": "Undo last action",
        "shortcut": "Ctrl+Z",
    },
}