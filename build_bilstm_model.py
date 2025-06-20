import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Bidirectional, LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

if __name__ == "__main__" : 
    # Load data set
    df = pd.read_csv("training_dataset.csv")
    features = df[["pm25", "temperature", "humidity"]].values

    # Normalize data
    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(features)

    # Create sequences (12 time steps)
    x, y = [], []
    for i in range(12, len(scaled_features)) : 
        x.append(scaled_features[i-12:i])
        y.append(scaled_features[i, 0])
    x, y = np.array(x), np.array(y)

    # Split data
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.2, random_state = 42)

    # Build Multi-Dense Layer BiLSTM model
    model = Sequential([
        Bidirectional(LSTM(50, return_sequences = True), input_shape = (12, 3)),
        Bidirectional(LSTM(50)),
        Dense(64, activation="relu"),
        Dense(32, activation="relu"),
        Dense(1)
    ])
    model.compile(optimizer = "adam", loss = "mse")

    # Train model
    model.fit(x_train, y_train, epochs = 20, batch_size = 32, validation_data = (x_test, y_test), verbose = 1)

    # Save model and scaler
    model.save("pm25_bilstm_model.h5")
    np.save("scaler.npy", scaler)

    print("Model trained and saved as pm25_bilstm_model.h5")