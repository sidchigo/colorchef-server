from sklearn.cluster import KMeans
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

def extract_colors(img, count = 3):
    # get image from API and read it
    image = np.array(Image.open(BytesIO(img)).convert('RGB'))

    # resize image to 100x100
    # Resize helps in reducing time for kmeans
    res = cv2.resize(image, dsize=(100, 100), interpolation=cv2.INTER_NEAREST)

    # make image data 1D
    image = res.reshape((res.shape[0] * res.shape[1], 3))

    # process image data with kmeans
    clt = KMeans(n_clusters = count, max_iter=150)
    clt.fit(image)
    color_list = np.ceil(clt.cluster_centers_).astype("int")
    palette = []
    for color in color_list:
        palette.append(f'rgb({color[0]}, {color[1]}, {color[2]})')
    return palette