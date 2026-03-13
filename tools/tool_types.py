#tool_types.py
from enum import Enum

class ToolType(Enum):
    PENCIL = "pencil"
    LINE = "line"
    POLYLINE = "polyline"
    CURVE = "curve"
    POLYCURVE = "polycurve"
    ERASER = "eraser"
    TEXT = "text"
    UNDO = "undo"