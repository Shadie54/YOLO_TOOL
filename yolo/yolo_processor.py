# yolo_processor.py
import os
import cv2

class YoloProcessor:
    """
    Trieda na načítanie YOLO modelu a spracovanie obrázka.
    Lazy loading: model sa načíta až pri prvom použití, aby sa GUI spustilo rýchlejšie.
    """

    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.yolo_auto = False

    def load_model(self):
        """Načíta YOLO model iba raz."""
        if self.model is None:
            os.environ["YOLO_OFFLINE"] = "true"  # zabráni automatickým update checkom
            from ultralytics import YOLO  # lazy import
            self.model = YOLO(self.model_path)
            self.model.to("cpu")

    def process(self, image):
        """Spustí YOLO detekciu na obrázku a vráti obrázok s vykreslenými boxami."""
        self.load_model()
        results = self.model(image, device="cpu")[0]

        if results.boxes is None:
            return image

        img = image.copy()
        boxes = results.boxes.xyxy.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy()
        confs = results.boxes.conf.cpu().numpy()

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            cls = int(classes[i])
            conf = confs[i]

            # ---------- Špeciálna úprava pre "foto" ----------
            if cls == 1:
                x2 = int(x1 + (x2 - x1) * 2.4)

            color = (0, 255, 0) if cls == 1 else (0, 0, 255)
            label = "foto" if cls == 1 else "arrow"

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                img,
                f"{label} {conf:.2f}",
                (x1, max(y1 - 5, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

        return img

    def process_with_boxes(self, image):
        """
        Spustí detekciu a vráti list bounding boxov vo formáte:
        [(x1, y1, x2, y2, cls), ...]
        """
        self.load_model()
        results = self.model(image, device="cpu")[0]
        boxes_out = []

        if results.boxes is None:
            return boxes_out

        boxes = results.boxes.xyxy.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy()

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            cls = int(classes[i])

            # ---------- Špeciálna úprava pre "foto" ----------
            if cls == 1:  # foto
                x2 = int(x1 + (x2 - x1) * 2.5)

            boxes_out.append((x1, y1, x2, y2, cls))

        return boxes_out

    def toggle_auto(self):
        self.yolo_auto = not self.yolo_auto
        print(f"[DEBUG] YoloProcessor.toggle_auto called, yolo_auto={self.yolo_auto}")
        return self.yolo_auto