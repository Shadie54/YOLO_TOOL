from PyQt6.QtWidgets import QApplication, QWidget, QPushButton
from tools.tool_registry import TOOL_REGISTRY
from tools.tool_types import ToolType
from gui_main import MainWindow  # tvoja trieda MainWindow

app = QApplication([])

window = MainWindow(None)  # YOLO model nie je potrebný
dummy_parent = QWidget()  # parent pre headless tlačidlá

# naplni tool_buttons
window.tool_buttons = {}
for tool_enum, props in TOOL_REGISTRY.items():
    btn = QPushButton(dummy_parent)  # parent je nutný, aby nepadlo
    btn.setStyleSheet("")
    window.tool_buttons[tool_enum] = btn

# test highlight
for tool_enum in TOOL_REGISTRY.keys():
    print(f"Selecting {tool_enum.name}")
    window.select_tool(tool_enum)
    for t, btn in window.tool_buttons.items():
        state = "highlighted" if "lightblue" in btn.styleSheet() else "normal"
        print(f"  {t.name}: {state}")

# toggle off
print("Toggling tool off")
window.select_tool(list(TOOL_REGISTRY.keys())[0])
for t, btn in window.tool_buttons.items():
    state = "highlighted" if "lightblue" in btn.styleSheet() else "normal"
    print(f"  {t.name}: {state}")