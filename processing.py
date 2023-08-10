import numpy as np
import cv2

#path_image_tiff = "./21-07-23/images/flir_thermal_16gray_2023_07_21_12_31_36_852653.tiff"
path_image_tiff = "./21-07-23/images/flir_thermal_16gray_2023_07_21_12_29_29_369441.tiff"

gray16_image = cv2.imread(path_image_tiff, cv2.IMREAD_ANYDEPTH)
print(gray16_image)
im_shape = gray16_image.shape

gray8_image = np.zeros(im_shape, dtype = np.uint8)
gray8_image = cv2.normalize(gray16_image, gray8_image,0, 255, cv2.NORM_MINMAX)
gray8_image = np.uint8(gray8_image)

ret, thresh = cv2.threshold(gray8_image, 
                40, 
                255, 
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

# Encontrar un area de pimer plano segura
dist_transform = cv2.distanceTransform(thresh, cv2.DIST_L2, 5)
cv2.normalize(dist_transform, dist_transform, 0, 1.0, cv2.NORM_MINMAX)

cv2.namedWindow("thresh", cv2.WINDOW_NORMAL)
cv2.resizeWindow("thresh", 640, 480)
cv2.imshow('thresh', thresh)

cv2.namedWindow("Distance Transform Image", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Distance Transform Image", 640, 480)
cv2.imshow('Distance Transform Image', dist_transform)

_, dist = cv2.threshold(dist_transform, 0.4, 1.0, cv2.THRESH_BINARY)
# Dilate a bit the dist image
#kernel1 = np.ones((3,3), dtype=np.uint8)
kernel1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

dist = cv2.dilate(dist, kernel1)
cv2.imshow('Peaks', dist)
cv2.resizeWindow("Peaks", 640, 480)
cv2.imshow("Peaks", gray8_image)

dist_8u = dist.astype('uint8')

contours, _ = cv2.findContours(dist_8u, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# sure background area
sure_bg = cv2.dilate(gray8_image, kernel1, iterations=3)

#foreground area
ret, sure_fg = cv2.threshold(dist, 0.5 * dist.max(), 255, cv2.THRESH_BINARY)
sure_fg = sure_fg.astype(np.uint8)  
cv2.imshow("sure_fg",sure_fg)

# unknown area
unknown = cv2.subtract(sure_bg, sure_fg)
cv2.imshow("unknown",unknown)

ret, markers = cv2.connectedComponents(sure_fg)
  
# Add one to all labels so that background is not 0, but 1
markers += 1
# mark the region of unknown with zero
markers[unknown == 255] = 0
gray = cv2.cvtColor(gray8_image, cv2.COLOR_GRAY2BGR)

markers = cv2.watershed(gray, markers)
gray[markers == -1] = [255,0,0]

cv2.namedWindow("gray", cv2.WINDOW_NORMAL)
cv2.resizeWindow("gray", 640, 480)
cv2.imshow('gray', gray)
#markers = np.zeros(dist.shape, dtype=np.uint8)
## Draw the foreground markers
#for i in range(len(contours)):
#    cv2.drawContours(markers, contours, i, (i+1), -1)
# Draw the background marker
#markers = cv2.circle(markers, (5,5), 3, (255,255,255), -1)
#markers_8u = (markers * 10).astype('uint8')
#cv2.imshow('Markers', markers_8u)
#cv2.resizeWindow("Markers", 640, 480)
#cv2.imshow("Markers", gray8_image)

# Perform the watershed algorithm

#markers = cv2.watershed(gray8_image, markers)
#mark = markers.astype('uint8')
#mark = cv2.bitwise_not(mark)



cv2.namedWindow("gray8", cv2.WINDOW_NORMAL)
cv2.resizeWindow("gray8", 640, 480)
cv2.imshow("gray8", gray8_image)

cv2.waitKey(0)