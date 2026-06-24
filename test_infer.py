import cv2
import numpy as np
from tensorflow.keras.models import load_model

model_path = r'c:\Users\HP\Desktop\Deacnproyect\ai_models\pneumonia_detection_model.h5'
image_path = r'c:\Users\HP\Desktop\inteligencia artifiical\chest_xray\train\PNEUMONIA\person1000_bacteria_2931.jpeg'

model = load_model(model_path)

img_array = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
img_resized = cv2.resize(img_array, (150, 150))
img_array = np.array(img_resized) / 255.0
img_input = img_array.reshape(1, 150, 150, 1)

pred = model.predict(img_input)
prob = float(pred[0][0])
print(f"Probabilidad de neumonía en la imagen de prueba: {prob}")

