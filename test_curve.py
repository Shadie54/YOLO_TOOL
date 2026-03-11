import cv2
import numpy as np

canvas = np.ones((700, 1000, 3), dtype=np.uint8) * 255

points = []
preview = None
brush_size = 2


def catmull_rom(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2 * p1)
        + (-p0 + p2) * t
        + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
        + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
    )


def draw_curve(img, pts):
    if len(pts) < 2:
        return

    # line for 2 points
    if len(pts) == 2:
        cv2.line(img, pts[0], pts[1], (0, 0, 0), brush_size)
        return

    # spline for 3+ points
    p = [pts[0]] + pts + [pts[-1]]

    for i in range(len(p) - 3):
        p0 = np.array(p[i])
        p1 = np.array(p[i + 1])
        p2 = np.array(p[i + 2])
        p3 = np.array(p[i + 3])

        prev = None

        for t in np.linspace(0, 1, 50):
            pt = catmull_rom(p0, p1, p2, p3, t)
            pt = (int(pt[0]), int(pt[1]))

            if prev is not None:
                cv2.line(img, prev, pt, (0, 0, 0), brush_size)

            prev = pt


def redraw():
    img = canvas.copy()

    temp_points = points.copy()
    if preview is not None:
        temp_points.append(preview)

    # preview curve
    draw_curve(img, temp_points)

    # red points
    for p in points:
        cv2.circle(img, p, 4, (0, 0, 255), -1)

    return img


def mouse(event, x, y, flags, param):
    global preview, points, canvas

    if event == cv2.EVENT_MOUSEMOVE:
        preview = (x, y)

    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))

    if event == cv2.EVENT_RBUTTONDOWN:
        points.clear()


cv2.namedWindow("Curve Tool Test")
cv2.setMouseCallback("Curve Tool Test", mouse)

while True:

    img = redraw()
    cv2.imshow("Curve Tool Test", img)

    key = cv2.waitKey(10)

    if key == 13:  # ENTER -> finalize
        draw_curve(canvas, points)
        points.clear()

    if key == 26:  # CTRL+Z
        if points:
            points.pop()

    if key == 27:  # ESC
        points.clear()

    if key == ord("q"):
        break


cv2.destroyAllWindows()