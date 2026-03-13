# test_toolbar.py
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize

# ------------------------- TOOLBAR REGISTRY SIM -------------------------
class MainToolbar:
    OPEN, YOLO, SAVE = range(3)

ICON_PATH = "assets/icons/"

MAIN_TOOLBAR_REGISTRY = {
    MainToolbar.OPEN: {"icon": "open.png", "tooltip": "Open folder", "callback": "open_callback"},
    MainToolbar.YOLO: {"icon": "yolo.png", "tooltip": "YOLO Auto", "callback": "toggle_yolo_auto"},
    MainToolbar.SAVE: {"icon": "save.png", "tooltip": "Save", "callback": "save_callback"},
}

# ------------------------- FAKE YOLO PROCESSOR -------------------------
class FakeYoloProcessor:
    def __init__(self):
        self.yolo_auto = False

    def toggle_auto(self):
        self.yolo_auto = not self.yolo_auto
        return self.yolo_auto

# ------------------------- TEST WINDOW -------------------------
class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toolbar YOLO Test")
        self.resize(300, 200)

        self.yolo = FakeYoloProcessor()
        self.tool_buttons = {}

        layout = QHBoxLayout()
        self.setLayout(layout)

        # vytvorenie toolbaru
        for tool_enum, props in MAIN_TOOLBAR_REGISTRY.items():
            btn = QPushButton()
            # nastavíme ikonku podľa stavu
            if tool_enum == MainToolbar.YOLO:
                icon_file = "yolo_auto.png" if self.yolo.yolo_auto else "yolo.png"
            else:
                icon_file = props["icon"]

            btn.setIcon(QIcon(ICON_PATH + icon_file))
            btn.setIconSize(QSize(64, 64))
            btn.setToolTip(props["tooltip"])

            # pripojíme callback
            callback_name = props["callback"]
            if callback_name == "toggle_yolo_auto":
                btn.clicked.connect(self.toggle_yolo_auto)
            else:
                btn.clicked.connect(lambda checked=False, n=callback_name: print(f"{n} clicked"))

            layout.addWidget(btn)
            self.tool_buttons[tool_enum] = btn

    def toggle_yolo_auto(self):
        # prepne stav a ikonku
        new_state = self.yolo.toggle_auto()
        icon_file = "yolo_auto.png" if new_state else "yolo.png"
        btn = self.tool_buttons[MainToolbar.YOLO]
        btn.setIcon(QIcon(ICON_PATH + icon_file))
        print("YOLO Auto ON" if new_state else "YOLO Auto OFF")


# ------------------------- MAIN -------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())