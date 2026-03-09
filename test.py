import sys
import os
import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from ultralytics import YOLO
import cv2

# -------- Worker pre YOLO detekciu --------
class YoloTestWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model, image):
        super().__init__()
        self.model = model
        self.image = image.copy() if image is not None else None

    def run(self):
        try:
            print("[DEBUG] Worker started")
            print(f"[DEBUG] Model: {self.model}")
            print(f"[DEBUG] Image shape: {self.image.shape if self.image is not None else 'None'}")

            # YOLO forward
            results = self.model(self.image, device="cpu")[0]

            print("[DEBUG] Model forward done")
            print(f"[DEBUG] Number of boxes: {len(results.boxes.xyxy) if results.boxes else 0}")

            self.finished.emit()
        except Exception as e:
            print(f"[ERROR] Exception in worker: {e}")
            self.error.emit(str(e))

# -------- MAIN TEST --------
if __name__ == "__main__":

    # cesta k modelu
    model_path = os.path.join("models", "best.pt")
    if not os.path.isfile(model_path):
        print(f"Model file not found: {model_path}")
        sys.exit(1)

    print("Loading YOLO model (CPU)...")
    yolo_model = YOLO(model_path)
    yolo_model.to("cpu")
    print("YOLO model loaded!")

    # test image (dummy alebo načítanie z disk)
    test_image = np.zeros((512, 512, 3), dtype=np.uint8)

    # -------- Spustenie worker v QThread --------
    thread = QThread()
    worker = YoloTestWorker(yolo_model, test_image)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(lambda: print("[DEBUG] Worker finished"))
    worker.finished.connect(thread.quit)
    thread.finished.connect(thread.deleteLater)
    worker.error.connect(lambda msg: print(f"[DEBUG] Worker error: {msg}"))

    print("Starting worker thread...")
    thread.start()
    thread.wait()  # počkáme na dokončenie
    print("Test complete")