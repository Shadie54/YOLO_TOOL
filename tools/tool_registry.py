from tools.tool_types import ToolType

ICON_PATH = "assets/icons/"

TOOL_REGISTRY = {
    ToolType.FREEHAND: {
        "icon": ICON_PATH + "pencil.png",
        "tooltip": "Freehand drawing",
        "shortcut": "F",
    },
    ToolType.LINE: {
        "icon": ICON_PATH + "line.png",
        "tooltip": "Draw line",
        "shortcut": "L",
    },
    ToolType.WHITE: {
        "icon": ICON_PATH + "del.png",
        "tooltip": "Erase (white brush)",
        "shortcut": "E",
    },
    ToolType.TEXT: {
        "icon": ICON_PATH + "text.png",
        "tooltip": "Insert text (WORK IN PROGRESS)",
        "shortcut": "T",
    },
    ToolType.UNDO: {
        "icon": ICON_PATH + "undo.png",
        "tooltip": "Undo last action (WORK IN PROGRESS)",
        "shortcut": "Ctrl+Z",
    },
}