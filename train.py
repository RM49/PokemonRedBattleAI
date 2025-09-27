# Takes pokemon data csv and gives a model

import tensorflow as tf
import csv
import numpy as np

DATA_FILE = "pokemon_data_parallel.csv"

inputs = []
outputs = []

with open(DATA_FILE, newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        numeric_row = [float(i) for i in row]

        outputs.append(numeric_row[-1:])
        inputs.append(numeric_row[:-1])

INPUT_LENGTH = len(inputs[1])

inputs = np.array(inputs)
outputs = np.array(outputs)

print(len(inputs))

model = tf.keras.models.Sequential([
  tf.keras.layers.Normalization(input_shape=[INPUT_LENGTH]),
  tf.keras.layers.Dense(128, activation='relu'),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(64, activation='relu'),
  tf.keras.layers.Dense(16, activation='relu'),
  tf.keras.layers.Dense(1)
])


model.compile(optimizer='adam',
            loss='mse',
            metrics=['mae']) # loss functions arbitrary

model.fit(inputs, outputs, epochs=50, batch_size=32, validation_split=0.2, verbose=1)

model.save_weights('pokmonmodel.weights.h5')