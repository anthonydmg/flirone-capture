import cv2

image_gray = cv2.imread("images/flir_thermal_16gray_1669063520919.tiff", cv2.IMREAD_ANYDEPTH)
print(image_gray)
print(image_gray.shape)
cv2.imshow("Image",image_gray)
cv2.waitKey(0)