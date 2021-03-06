# region Import libraries
from src.utils._attention import attention_3d_block
from src.classes.Metrics import metrics
from keras import Model as KerasModel
from keras.layers import Dense, Bidirectional, Dropout, Conv1D, MaxPool1D, Flatten, LSTM, Input, GRU, TimeDistributed
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score


# endregion


class Model(object):
    def __init__(self, x, y, opts):
        self.model = None
        self.x = x
        self.y = y
        self.input_dims = opts["input_dims"]
        self.model_type = opts["model_type"]
        self.activation_func = "sigmoid"
        self.loss_func = "binary_crossentropy"
        self.optimizer = "adam"
        self.metrics = ["accuracy"]
        self.activate_attention = opts["activate_attention"]
        self.dropout = opts["dropout"]
        try:
            if opts["load_weights"]:
                self.load_weights = True
                self.weights_path = opts["weights_path"]
            else:
                self.load_weights = False
        except KeyError:
            self.load_weights = False
        if self.model_type == "cnn":
            self.cnn_opts = {
                "kernel_size": opts["kernel_size"],
                "filters": opts["filters"],
                "pool_size": opts["pool_size"],
                "strides": opts["strides"],
                "padding": "valid",
                "activation": "relu",
            }
        elif self.model_type == "blstm":
            self.lstm_opts = {
                "lstm_units": opts["lstm_units"]
            }
        else:
            pass

    def build_model(self):
        inputs = Input(shape=(self.input_dims[0], self.input_dims[1]))
        if self.model_type == "cnn":
            cnn_out = Conv1D(
                filters=self.cnn_opts["filters"],
                kernel_size=self.cnn_opts["kernel_size"],
                strides=self.cnn_opts["strides"],
                padding=self.cnn_opts["padding"],
                activation=self.cnn_opts["activation"],
            )(inputs)
            max_pool_out = MaxPool1D(pool_size=self.cnn_opts["pool_size"])(cnn_out)
            dropout_out = Dropout(self.dropout)(max_pool_out)
        else:
            lstm_out = Bidirectional(LSTM(units=self.lstm_opts["lstm_units"], return_sequences=True))(inputs)
            dropout_out = Dropout(self.dropout)(lstm_out)
        if self.activate_attention:
            attention_out = attention_3d_block(dropout_out)
        else:
            attention_out = Flatten()(dropout_out)
        output = Dense(1, activation=self.activation_func)(attention_out)
        self.model = KerasModel(inputs=[inputs], outputs=[output])
        if self.load_weights:
            self.model.load_weights(self.weights_path)
        self.model.compile(loss=self.loss_func, optimizer=self.optimizer, metrics=self.metrics)

    def fit_model(self, epochs, batch_size, validation_data):
        self.model.fit(self.x,
                       self.y,
                       epochs=epochs,
                       batch_size=batch_size,
                       validation_data=validation_data,
                       verbose=True,
                       callbacks=[metrics])

    def calculate_metrics(self, x_test, y_test):
        preds = np.array([i[0].round() for i in self.model.predict(x_test)])
        precision = precision_score(y_test, preds)
        recall = recall_score(y_test, preds)
        f1 = f1_score(y_test, preds)
        return precision, recall, f1
