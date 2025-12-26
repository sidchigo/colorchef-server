from sklearn.cluster import KMeans
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

def extract_colors(img_bytes, count=5):
    # 1. Load image and convert to RGB
    image = np.array(Image.open(BytesIO(img_bytes)).convert('RGB'))

    # 2. Resize with INTER_AREA (best for downsampling/shrinking)
    # Reducing to 100x100 significantly speeds up K-Means
    res = cv2.resize(image, dsize=(100, 100), interpolation=cv2.INTER_AREA)

    # 3. CONVERT TO LAB COLOR SPACE
    # Why? Lab space clusters colors based on human perception. 
    # This prevents your palettes from looking "muddy" or "washed out".
    lab_image = cv2.cvtColor(res, cv2.COLOR_RGB2LAB)
    data = lab_image.reshape((lab_image.shape[0] * lab_image.shape[1], 3))

    # 4. K-Means Clustering
    # random_state=42 ensures the same image always yields the same palette
    clt = KMeans(n_clusters=count, n_init="auto", max_iter=200, random_state=42)
    clt.fit(data)

    # 5. Convert Cluster Centers back to RGB
    centers_lab = np.uint8([clt.cluster_centers_])
    centers_rgb = cv2.cvtColor(centers_lab, cv2.COLOR_LAB2RGB)[0]

    # 6. Return list of RGB strings for your existing frontend logic
    palette = [f'rgb({c[0]}, {c[1]}, {c[2]})' for c in centers_rgb]
    return palette