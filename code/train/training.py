# import tensorflow as tf
# from tensorflow.keras.preprocessing.image import ImageDataGenerator
# from tensorflow.keras import layers, models, applications

# # 1. Path to your manually extracted data
# DATA_PATH = 'data/Garbage classification/Garbage classification'


# # 2. Data Augmentation (Makes the model more robust)
# datagen = ImageDataGenerator(
#     rescale=1./255,
#     validation_split=0.2, # Uses 20% for testing
#     rotation_range=40,
#     width_shift_range=0.2,
#     height_shift_range=0.2,
#     shear_range=0.2,
#     zoom_range=0.2,
#     horizontal_flip=True,
#     fill_mode='nearest'
# )

# train_generator = datagen.flow_from_directory(
#     DATA_PATH,
#     target_size=(224, 224),
#     batch_size=32,
#     class_mode='categorical',
#     subset='training'
# )

# validation_generator = datagen.flow_from_directory(
#     DATA_PATH,
#     target_size=(224, 224),
#     batch_size=32,
#     class_mode='categorical',
#     subset='validation'
# )

# # 3. Build Model (MobileNetV2 is best for Raspberry Pi later)
# base_model = applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
# base_model.trainable = False 

# model = models.Sequential([
#     base_model,
#     layers.GlobalAveragePooling2D(),
#     layers.Dense(128, activation='relu'),
#     layers.Dropout(0.5),
#     layers.Dense(train_generator.num_classes, activation='softmax')
# ])

# model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# # 4. Train
# print("Starting training...")
# model.fit(train_generator, validation_data=validation_generator, epochs=10)

# # 5. Save the model
# model.save('trash_classifier.h5')
# print("Model saved as trash_classifier.h5")




import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, models, applications
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

# --- PART 1: YOUR ORIGINAL TRAINING CODE (with minor additions) ---

# 1. Path to your manually extracted data
DATA_PATH = '../../data/Garbage classification/Garbage classification'

# 2. Data Augmentation (Makes the model more robust)
# We create two generators: one for training (with augmentation) and one for validation (no augmentation)
train_datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2, # Uses 20% for testing
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

# For validation, we only rescale the images
validation_datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2
)

train_generator = train_datagen.flow_from_directory(
    DATA_PATH,
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    subset='training',
    shuffle=True # Shuffle training data
)

validation_generator = validation_datagen.flow_from_directory(
    DATA_PATH,
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    subset='validation',
    shuffle=False # IMPORTANT: Keep validation data in order for evaluation
)

# 3. Build Model (MobileNetV2 is best for Raspberry Pi later)
base_model = applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
base_model.trainable = False 

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(train_generator.num_classes, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# 4. Train and Capture History
print("Starting training...")
# The fit method returns a "history" object with the metrics per epoch
history = model.fit(
    train_generator, 
    validation_data=validation_generator, 
    epochs=10
)

# 5. Save the model
model.save('trash_classifier.h5')
print("Model saved as trash_classifier.h5")


# --- PART 2: NEW CODE FOR EVALUATION AND VISUALIZATION ---

# 6. Generate Predictions on the Validation Set
print("\nGenerating predictions for evaluation...")
# Reset the validation generator before prediction
validation_generator.reset()
# Use model.predict to get the probability for each class
Y_pred = model.predict(validation_generator, steps=len(validation_generator))
# Convert probabilities to class labels (e.g., [0.1, 0.9] -> 1)
y_pred = np.argmax(Y_pred, axis=1)

# Get the true labels from the generator
y_true = validation_generator.classes
# Get the class names
class_names = list(validation_generator.class_indices.keys())

# 7. Create the Classification Report (Table 1)
print("\n--- Classification Report ---")
report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
# Print the report in a nicely formatted way
print(classification_report(y_true, y_pred, target_names=class_names))

# 8. Create the Confusion Matrix (Chart 2)
print("\n--- Confusion Matrix ---")
cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
plt.title('Confusion Matrix')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.savefig('confusion_matrix.png') # Save the plot
plt.show()

# 9. Plot Training & Validation Accuracy/Loss (Chart 1)
print("\n--- Plotting Training History ---")
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs_range = range(len(acc))

plt.figure(figsize=(12, 6))

# Plot Training and Validation Accuracy
plt.subplot(1, 2, 1)
plt.plot(epochs_range, acc, label='Training Accuracy')
plt.plot(epochs_range, val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.title('Training and Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')

# Plot Training and Validation Loss
plt.subplot(1, 2, 2)
plt.plot(epochs_range, loss, label='Training Loss')
plt.plot(epochs_range, val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.title('Training and Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')

plt.tight_layout()
plt.savefig('training_history.png') # Save the plot
plt.show()

print("\nEvaluation complete. Charts and reports saved.")