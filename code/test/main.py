# import cv2
# import numpy as np
# import tensorflow as tf
# from collections import deque

# # 1. LOAD THE MODEL
# # Ensure this filename matches the one you saved in train_model.py
# try:
#     model = tf.keras.models.load_model('../../model/trash_classifier.h5')
   
#     print("Model loaded successfully!")
# except:
#     print("Error: 'trash_classifier.h5' not found. Did you run the training script?")
#     exit()

# # 2. DEFINE LABELS
# # These MUST be in alphabetical order (the same way Windows/Linux sorts folders)
# LABELS = ['Cardboard', 'Glass', 'Metal', 'Paper', 'Plastic', 'Trash']

# # 3. CAMERA & BUFFER SETUP
# cap = cv2.VideoCapture(0)
# # Buffer stores last 20 frames to provide a "Smooth" average prediction
# pred_buffer = deque(maxlen=20)

# print("Smart Bin System Active. Press 'q' to quit.")

# while True:
#     ret, frame = cap.read()
#     if not ret: break
    
#     # Mirror the frame for easier object positioning
#     frame = cv2.flip(frame, 1)

#     # --- DEFINE FOCUS AREA ---
#     h, w, _ = frame.shape
#     box_size = 300
#     x1, y1 = (w - box_size) // 2, (h - box_size) // 2
#     x2, y2 = x1 + box_size, y1 + box_size
    
#     # Crop the center area for the AI
#     roi = frame[y1:y2, x1:x2]

#     # --- PREPROCESS FOR AI ---
#     # MobileNetV2 expects 224x224 images normalized between 0 and 1
#     img = cv2.resize(roi, (224, 224))
#     img_array = img.astype('float32') / 255.0
#     img_array = np.expand_dims(img_array, axis=0)

#     # --- INFERENCE ---
#     predictions = model.predict(img_array, verbose=0)[0]
#     pred_buffer.append(predictions)
    
#     # Calculate Average probabilities across the buffer
#     avg_preds = np.mean(pred_buffer, axis=0)
    
#     # Get the index of the highest probability
#     class_idx = np.argmax(avg_preds)
#     confidence = avg_preds[class_idx]
#     detected_label = LABELS[class_idx]

#     # --- UI DESIGN ---
#     # Change color based on confidence (Green = Sure, Red = Unsure)
#     color = (0, 255, 0) if confidence > 0.7 else (0, 0, 255)
    
#     # Draw the main scanning box
#     cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
#     # Display the Name and Confidence
#     label_text = f"{detected_label}: {int(confidence*100)}%"
#     cv2.putText(frame, label_text, (x1, y1 - 15), 
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
#     # Show the probability for all classes (Optional Debugging info)
#     y_offset = 30
#     for i, label in enumerate(LABELS):
#         prob = avg_preds[i] * 100
#         cv2.putText(frame, f"{label}: {int(prob)}%", (10, y_offset + (i*25)), 
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

#     # --- SHOW WINDOW ---
#     cv2.imshow('Smart Bin Multi-Trash Detector', frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()

# cv2.destroyAllWindows()




import cv2
import numpy as np
import tensorflow as tf
from collections import deque

# Load the model
model = tf.keras.models.load_model('../../model/trash_classifier.h5')
LABELS = ['Cardboard', 'Glass', 'Metal', 'Paper', 'Plastic', 'Trash']

cap = cv2.VideoCapture(0)


pred_buffer = deque(maxlen=30) 

print("System Active. Hold object STILL in the box.")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)

    # 1. Focus on the center
    h, w, _ = frame.shape
    box_size = 280
    x1, y1 = (w - box_size) // 2, (h - box_size) // 2
    x2, y2 = x1 + box_size, y1 + box_size
    roi = frame[y1:y2, x1:x2]

    # 2. Pre-process
    img = cv2.resize(roi, (224, 224))
    img_array = img.astype('float32') / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # 3. Predict & Buffer
    preds = model.predict(img_array, verbose=0)[0]
    pred_buffer.append(preds)
    
    # Calculate Average Confidence
    avg_preds = np.mean(pred_buffer, axis=0)
    class_idx = np.argmax(avg_preds)
    confidence = avg_preds[class_idx]

    # --- THE ANTI-CONFUSION LOGIC ---
    # Only show a label if confidence is very high (85%+)
    if confidence > 0.85:
        final_label = f"DETECTED: {LABELS[class_idx]}"
        color = (0, 255, 0) # Green
    elif confidence > 0.50:
        final_label = "Thinking... keep still"
        color = (0, 255, 255) # Yellow
    else:
        final_label = "Place Object in Box"
        color = (0, 0, 255) # Red

    # UI Feedback
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(frame, final_label, (x1, y1 - 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    # Display Confidence Bar
    cv2.rectangle(frame, (x1, y2 + 10), (x1 + int(box_size * confidence), y2 + 25), color, -1)

    cv2.imshow('Smart Bin - Stabilized View', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()