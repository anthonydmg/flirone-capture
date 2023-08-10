import numpy as np
import cv2

path_image_tiff = "./21-07-23/images/flir_thermal_16gray_2023_07_21_12_31_36_852653.tiff"

gray16_image = cv2.imread(path_image_tiff, cv2.IMREAD_ANYDEPTH)
print(gray16_image)
im_shape = gray16_image.shape

gray8_image = np.zeros(im_shape, dtype = np.uint8)
gray8_image = cv2.normalize(gray16_image, gray8_image,0, 255, cv2.NORM_MINMAX)
gray8_image = np.uint8(gray8_image)
inferno_palette = cv2.applyColorMap(gray8_image, cv2.COLORMAP_INFERNO)
jet_palette = cv2.applyColorMap(gray8_image, cv2.COLORMAP_JET)
viridis_palette = cv2.applyColorMap(gray8_image, cv2.COLORMAP_VIRIDIS)

cv2.namedWindow("gray8", cv2.WINDOW_NORMAL)
cv2.resizeWindow("gray8", 640, 480)
cv2.imshow("gray8", gray8_image)

cv2.namedWindow("inferno", cv2.WINDOW_NORMAL)
cv2.resizeWindow("inferno", 640, 480)
cv2.imshow("inferno", inferno_palette)
cv2.namedWindow("jet", cv2.WINDOW_NORMAL)
cv2.resizeWindow("jet", 640, 480)
cv2.imshow("jet", jet_palette)
cv2.namedWindow("viridis", cv2.WINDOW_NORMAL)
cv2.resizeWindow("viridis", 640, 480)
cv2.imshow("viridis", viridis_palette)
cv2.waitKey(0)