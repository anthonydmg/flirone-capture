import cv2
file_image = "images/flir_visible_image_1675278558689.jpg"

img = cv2.imread(file_image)
_, img_encoded = cv2.imencode('.jpg', img)
print(img_encoded.shape)
cv2.imshow("Image", img)
cv2.waitKey(0)