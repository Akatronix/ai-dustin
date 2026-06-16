import tensorflow as tf

# Load your existing Keras model
model = tf.keras.models.load_model('../model/trash_classifier.h5')

# Convert the model
converter = tf.lite.TFLiteConverter.from_keras_model(model)
# Optional: Optimization (makes it faster/smaller)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

# Save the model
with open('trash_classifier.tflite', 'wb') as f:
    f.write(tflite_model)

print("Model converted to TFLite successfully!")