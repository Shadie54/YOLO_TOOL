import cv2
import numpy as np

img = np.ones((600,900,3),dtype=np.uint8)*255
points = []

def catmull_rom(p0,p1,p2,p3,t):
    t2 = t*t
    t3 = t2*t
    return (
        0.5*((2*p1) +
        (-p0+p2)*t +
        (2*p0-5*p1+4*p2-p3)*t2 +
        (-p0+3*p1-3*p2+p3)*t3)
    )

def draw_curve():
    if len(points) < 4:
        return

    for i in range(len(points)-3):
        p0=np.array(points[i])
        p1=np.array(points[i+1])
        p2=np.array(points[i+2])
        p3=np.array(points[i+3])

        prev=None
        for t in np.linspace(0,1,50):
            pt=catmull_rom(p0,p1,p2,p3,t)
            pt=(int(pt[0]),int(pt[1]))

            if prev is not None:
                cv2.line(img,prev,pt,(0,0,0),2)

            prev=pt

def mouse(event,x,y,flags,param):
    if event==cv2.EVENT_LBUTTONDOWN:
        points.append((x,y))
        cv2.circle(img,(x,y),4,(0,0,255),-1)
        draw_curve()

    if event==cv2.EVENT_RBUTTONDOWN:
        points.clear()
        img[:]=255

cv2.namedWindow("Curve test")
cv2.setMouseCallback("Curve test",mouse)

while True:
    cv2.imshow("Curve test",img)
    if cv2.waitKey(1)==27:
        break

cv2.destroyAllWindows()