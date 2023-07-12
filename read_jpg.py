from libjpeg import decode
import io 
with open('./images/flir_visible_image_2023_06_26_17_10_05_834229.jpg', 'rb') as f:
    # Returns a numpy array
    data = f.read()
    print(data)
    arr = decode(data)
    #print(arr)
## https://stackoverflow.com/questions/51442437/jpeg-decompression-on-raw-image-in-python

d = io.BytesIO()
print(d)