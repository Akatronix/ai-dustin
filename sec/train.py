import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models, applications
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
import os

# --- 1. SETTINGS & PATHS ---
DATA_PATH = '../data/Garbage classification/Garbage classification'
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS_PHASE_1 = 10
EPOCHS_PHASE_2 = 20

# --- 2. DATA PREPARATION ---
# Training with heavy augmentation for better generalization
train_datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2,
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    brightness_range=[0.8, 1.2], # Simulates different lighting conditions
    fill_mode='nearest'
)

# Validation only needs rescaling
val_datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)

train_generator = train_datagen.flow_from_directory(
    DATA_PATH,
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    shuffle=True
)

val_generator = val_datagen.flow_from_directory(
    DATA_PATH,
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    shuffle=False
)

# --- 3. MODEL BUILDING (PHASE 1: TRANSFER LEARNING) ---
base_model = applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
base_model.trainable = False  # Freeze the base

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.BatchNormalization(),
    layers.Dense(256, activation='relu'),
    layers.Dropout(0.4),
    layers.Dense(train_generator.num_classes, activation='softmax')
])

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# Callbacks for efficiency
callbacks = [
    tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True, monitor='val_loss'),
    tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=0.00001)
]

print("\n--- PHASE 1: Training the Head ---")
history1 = model.fit(train_generator, validation_data=val_generator, epochs=EPOCHS_PHASE_1, callbacks=callbacks)

# --- 4. MODEL REFINEMENT (PHASE 2: FINE-TUNING) ---
# Unfreeze the base model to tune high-level features
base_model.trainable = True

# We keep the first 100 layers frozen to avoid destroying pre-learned features
fine_tune_at = 100
for layer in base_model.layers[:fine_tune_at]:
    layer.trainable = False

# Recompile with a significantly lower learning rate
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
              loss='categorical_crossentropy',
              metrics=['accuracy'])

print("\n--- PHASE 2: Fine-Tuning later layers ---")
history2 = model.fit(train_generator, validation_data=val_generator, epochs=EPOCHS_PHASE_2, callbacks=callbacks)

# --- 5. EVALUATION & VISUALIZATION ---
print("\nEvaluating Model...")
val_generator.reset()
Y_pred = model.predict(val_generator)
y_pred = np.argmax(Y_pred, axis=1)
y_true = val_generator.classes
class_names = list(val_generator.class_indices.keys())

# Print Report
print("\nClassification Report:")
print(classification_report(y_true, y_pred, target_names=class_names))

# Plot Confusion Matrix
plt.figure(figsize=(10, 8))
sns.heatmap(confusion_matrix(y_true, y_pred), annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
plt.title('Confusion Matrix')
plt.savefig('confusion_matrix.png')

# --- 6. SAVE & CONVERT FOR RASPBERRY PI ---
# Save the standard Keras model
model.save('trash_classifier_full.h5')

# Convert to TFLite (Optimized for Pi)
print("\nConverting to TFLite...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT] # Quantization for speed
tflite_model = converter.convert()

with open('trash_classifier.tflite', 'wb') as f:
    f.write(tflite_model)

print("Setup Complete! Use 'trash_classifier.tflite' on your Raspberry Pi.")