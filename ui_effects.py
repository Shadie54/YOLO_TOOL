
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve


def start_pulsing_glow(widget, mode, start_blur=10, end_blur=30, duration=800):
    """
    Pulzujúci glow efekt pre tlačidlo alebo iný widget.
    """
    effect = QGraphicsDropShadowEffect(widget)
    effect.setOffset(0)

    if mode == "Delete":
        color = QColor(255, 0, 0, 180)
    else:
        color = QColor(0, 150, 255, 180)

    effect.setColor(color)
    effect.setBlurRadius(start_blur)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"blurRadius", widget)
    animation.setStartValue(start_blur)
    animation.setEndValue(end_blur)
    animation.setDuration(duration)
    animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    animation.setLoopCount(-1)
    animation.start()

    # Uložíme animáciu do widgetu, aby ju Garbage Collector nevymazal
    widget._pulse_animation = animation