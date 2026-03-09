import cv2


class YoloProcessor:
    """
    Trieda zodpovedná za načítanie YOLO modelu a spracovanie obrázka.
    Model sa načíta až pri prvom použití (lazy loading), aby sa GUI spustilo rýchlejšie.
    """

    def __init__(self, model_path):
        # cesta k YOLO modelu (.pt súbor)
        self.model_path = model_path

        # model sa inicializuje až pri prvom použití
        self.model = None

    def load_model(self):
        """
        Načíta YOLO model iba raz.
        Ak už je model načítaný, funkcia nič nerobí.
        """

        if self.model is None:
            print("metóda load_model sa spúšťa (YOLO_PROCESSOR.PY > load_model(self)")

            import os

            # zakáže Ultralytics knižnici pripájať sa na GitHub kvôli kontrole aktualizácií
            # bez tohto môže aplikácia zamrznúť alebo spadnúť na PC bez internetu
            os.environ["YOLO_OFFLINE"] = "true"

            # import až tu (lazy import), aby sa torch/ultralytics nenačítavali pri štarte GUI
            from ultralytics import YOLO

            # načítanie modelu zo súboru
            self.model = YOLO(self.model_path)

            # vynúti použitie CPU (stabilnejšie na rôznych PC a pri EXE distribúcii)
            self.model.to("cpu")

    def process(self, image):
        """
        Spustí YOLO detekciu na obrázku a vykreslí bounding boxy.
        """

        # zabezpečí, že model je načítaný
        self.load_model()

        # spustenie detekcie (vynútené CPU)
        results = self.model(image, device="cpu")[0]

        # ak model nenašiel žiadne objekty, vráti pôvodný obrázok
        if results.boxes is None:
            return image

        # vytvorí kópiu obrázka, do ktorej budeme kresliť detekcie
        img = image.copy()

        # získanie bounding boxov, tried a confidence hodnôt
        boxes = results.boxes.xyxy.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy()
        confs = results.boxes.conf.cpu().numpy()

        for i, box in enumerate(boxes):

            # súradnice bounding boxu
            x1, y1, x2, y2 = map(int, box)

            # trieda objektu
            cls = int(classes[i])

            # confidence modelu
            conf = confs[i]

            # farba boxu podľa triedy
            # zelená = foto
            # červená = arrow
            color = (0, 255, 0) if cls == 1 else (0, 0, 255)

            # textový label
            label = "foto" if cls == 1 else "arrow"

            # vykreslenie obdĺžnika
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

            # vykreslenie textu nad boxom
            cv2.putText(
                img,
                f"{label} {conf:.2f}",
                (x1, max(y1 - 5, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

        # vráti obrázok s vykreslenými detekciami
        return img