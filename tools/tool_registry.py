from tools.tool_types import ToolType

# definícia všetkých nástrojov GUI
TOOL_REGISTRY = {

    ToolType.FREEHAND: {
        "icon": "pencil.png",
        "tooltip": "Freehand drawing"
    },

    ToolType.LINE: {
        "icon": "line.png",
        "tooltip": "Draw line"
    },

    ToolType.WHITE: {
        "icon": "del.png",
        "tooltip": "Erase"
    },

    ToolType.TEXT: {
        "icon": "text.png",
        "tooltip": "Text tool"
    },

    ToolType.UNDO: {
        "icon": "undo.png",
        "tooltip": "Undo action"
    },

}