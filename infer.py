import sys
import cv2
import numpy as np
import os

def main():
    if len(sys.argv) < 3:
        sys.exit(1)
        
    model_path = sys.argv[1]
    image_path = sys.argv[2]
    
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    try:
        from tensorflow.keras.models import load_model
        model = load_model(model_path)
        img_array = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        img_resized = cv2.resize(img_array, (150, 150))
        img_array = np.array(img_resized) / 255.0
        img_input = img_array.reshape(1, 150, 150, 1)

        pred = model.predict(img_input, verbose=0)
        prob = float(pred[0][0])
        print(f"PROB:{prob}")
    except Exception as e:
        print(f"ERROR:{e}")

if __name__ == '__main__':
    main()
