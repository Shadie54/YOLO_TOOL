from enum import Enum

class ToolType(Enum):
    FREEHAND = "freehand"
    LINE = "line"
    CURVE = "curve"
    POLYCURVE = "polycurve"
    WHITE = "white"
    TEXT = "text"
    UNDO = "undo"