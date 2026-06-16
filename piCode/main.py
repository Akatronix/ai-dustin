import cv2
import numpy as np
import tflite_runtime.interpreter as tflite # Faster for Pi
from collections import deque

# 1. LOAD THE TFLITE MODEL
interpreter = tflite.Interpreter(model_path="trash_classifier.lite")
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

LABELS = ['Cardboard', 'Glass', 'Metal', 'Paper', 'Plastic', 'Trash']
cap = cv2.VideoCapture(0)
pred_buffer = deque(maxlen=30) 

print("TFLite System Active on Raspberry Pi.")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # 1. Focus Area (ROI)
    h, w, _ = frame.shape
    box_size = 280
    x1, y1 = (w - box_size) // 2, (h - box_size) // 2
    x2, y2 = x1 + box_size, y1 + box_size
    roi = frame[y1:y2, x1:x2]

    # 2. Pre-process (Matches MobileNetV2 requirements)
    img = cv2.resize(roi, (224, 224))
    img_array = img.astype('float32') / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # 3. TFLITE INFERENCE
    interpreter.set_tensor(input_details[0]['index'], img_array)
    interpreter.invoke()
    preds = interpreter.get_tensor(output_details[0]['index'])[0]
    
    pred_buffer.append(preds)
    
    # Calculate Average Confidence
    avg_preds = np.mean(pred_buffer, axis=0)
    class_idx = np.argmax(avg_preds)
    confidence = avg_preds[class_idx]

    # --- LOGIC & UI ---
    if confidence > 0.85:
        final_label = f"DETECTED: {LABELS[class_idx]}"
        color = (0, 255, 0)
    elif confidence > 0.50:
        final_label = "Thinking... keep still"
        color = (0, 255, 255)
    else:
        final_label = "Place Object in Box"
        color = (0, 0, 255)

    # Drawing
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(frame, final_label, (x1, y1 - 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    # Confidence Bar
    bar_width = int(box_size * confidence)
    cv2.rectangle(frame, (x1, y2 + 10), (x1 + bar_width, y2 + 25), color, -1)

    cv2.imshow('Smart Bin - TFLite Optimized', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()