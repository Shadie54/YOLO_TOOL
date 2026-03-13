# test_gui.py
import sys
from PyQt6.QtWidgets import QApplication
from gui_main import MainWindow
from yolo.yolo_processor import YoloProcessor

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # inicializácia YOLO (len dummy model, nemusí detekovať nič)
    model_path = "models/best.pt"
    yolo = YoloProcessor(model_path)
    yolo.load_model()

    # spustenie okna
    window = MainWindow(yolo)
    window.show()

    # Pridaj testovací obrázok (ak máš nejaký vo folderi)
    import cv2
    import numpy as np
    test_img = np.ones((512, 512, 3), dtype=np.uint8) * 200  # sivý obrázok
    window.cv_image = test_img
    window.image_label.set_image(test_img)
    window.image_label.redraw()

    print("Test GUI spustené. Skús Pencil, Eraser, Line, PolyLine, Curve, PolyCurve.")
    sys.exit(app.exec())