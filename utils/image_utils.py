import numpy as np

def blend_alpha(fg, bg):
    """
    fg: foreground RGBA image
    bg: background BGR image
    """
    alpha = fg[:, :, 3:] / 255.0
    blended = bg * (1 - alpha) + fg[:, :, :3] * alpha
    return blended.astype(np.uint8)