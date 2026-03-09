from PyQt6.QtGui import QCursor, QPixmap, QPainter, QColor, QPen


def create_brush_cursor(brush_size, color=(0, 0, 0)):
    """
    Vytvorí vlastný kurzor v tvare kruhu pre drawing mód.

    brush_size: polomer kruhu v pixeloch
    color: RGB tuple, farba kruhu
    """
    size = max(32, brush_size * 2 + 4)  # zabezpečí dostatočnú pixmapu
    pix = QPixmap(size, size)
    pix.fill(QColor(0, 0, 0, 0))  # transparentné pozadie

    painter = QPainter(pix)
    pen = QPen(QColor(*color))
    pen.setWidth(2)
    painter.setPen(pen)

    center = size // 2
    radius = brush_size
    painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)

    painter.end()
    return QCursor(pix, center, center)