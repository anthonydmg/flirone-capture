import cv2
import base64

file_image = "images/flir_visible_image_1675278558689.jpg"

img = cv2.imread(file_image)

## image to base64
_, img_buffer = cv2.imencode('.jpg', img)

img_base64 = base64.b64encode(img_buffer).decode('utf-8')

print(img_base64)
#M1
#frame = img_encoded.tobytes()
#img_base64 = base64.b64encode(frame)
#print(img_base64)


#print(img_encoded.shape)
#cv2.imshow("Image", img)
#cv2.waitKey(0)

## Ver esto como codifica y lo pone en el elemento para replicar esto
## https://ecode.dev/websocket-for-images-using-fastapi/
## Diferenciar del src directo del attr poner el tag image
## https://medium.com/csmadeeasy/send-and-receive-images-in-flask-in-memory-solution-21e0319dcc1
## Ver si como codificar
## https://python.plainenglish.io/build-a-computer-vision-web-api-with-flask-base64-like-imgix-814cb443aab7  

