# test.py
import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from canvas.image_canvas import ImageCanvas
from tools.tool_types import ToolType

# ------------------ jednoduchý logger ------------------
def dummy_log(msg):
    print(msg)

# ------------------ PyQt setup ------------------
app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout()
window.setLayout(layout)

# ------------------ Canvas ------------------
canvas = ImageCanvas()
canvas.log_callback = dummy_log  # zapneme logging pre nástroje

# testovací obrázok (prázdne čierne plátno)
cv_img = 255 * np.ones((480, 640, 3), dtype=np.uint8)
canvas.set_image(cv_img)

layout.addWidget(canvas)
window.show()

# ------------------ prepínanie nástrojov ------------------
# Pre rýchly test si môžeme prepínať ručne:
#canvas.drawing_engine.tool = ToolType.CURVE
#canvas.drawing_engine.tool = ToolType.POLYCURVE
canvas.drawing_engine.tool = ToolType.POLYLINE

print("Aktívny nástroj:", canvas.drawing_engine.tool)

sys.exit(app.exec())