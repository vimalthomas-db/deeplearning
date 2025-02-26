# -*- coding: utf-8 -*-
"""deploy_multilayerperceptron.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/12URCEVxRAH4r3s9eI6tDWWO6nLGe5yVO
"""

##############################################################################
#
# This python notebook creates a multilayerperceptron model that uses a collection
# of activation functions for creating and setting up nueral networks that are deep
# and hidden, which can be used for both classification (binary/multi-class) and regression
# like problems.
#
#     02/25/2025
#     Vimal Thomas Joseph
#
# Initial Draft
#
#############################################################################


import numpy as np
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from typing import Tuple


def batch_generator(train_x, train_y, batch_size):
    indices = np.arange(len(train_x))

    # shuffling for fair batch generation
    np.random.shuffle(indices)

    for i in range(0, len(train_x), batch_size):
        batch_idx = indices[i:i+batch_size]
        batch_x = train_x[batch_idx]
        batch_y = train_y[batch_idx]
        yield batch_x, batch_y






class ActivationFunction(ABC):
    @abstractmethod
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Computes the output of the activation function, evaluated on x

        Input args may differ in the case of softmax

        :param x (np.ndarray): input
        :return: output of the activation function
        """
        pass

    @abstractmethod
    def derivative(self, x: np.ndarray) -> np.ndarray:
        """
        Computes the derivative of the activation function, evaluated on x
        :param x (np.ndarray): input
        :return: activation function's derivative at x
        """
        pass


class Sigmoid(ActivationFunction):
    def forward(self, x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-x))

    def derivative(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x) * (1 - self.forward(x))




class Tanh(ActivationFunction):
    def forward(self, x: np.ndarray) -> np.ndarray:
        return np.tanh(x)

    def derivative(self, x: np.ndarray) -> np.ndarray:
        return 1 - np.tanh(x) ** 2


class Relu(ActivationFunction):
  def forward(self, x: np.ndarray) -> np.ndarray:
    return np.maximum(0, x)

  def derivative(self, x: np.ndarray) -> np.ndarray:
    return (x > 0).astype(float)


class Softmax(ActivationFunction):
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Computes the Softmax activation function.
        Uses a stability trick to prevent overflow.

        :param x: Input logits (batch_size, num_classes)
        :return: Softmax probabilities (batch_size, num_classes)
        """
        x_max = np.max(x, axis=-1, keepdims=True)
        exp_x = np.exp(x - x_max)
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def derivative(self, x: np.ndarray) -> np.ndarray:
        """
        Computes the Jacobian matrix of Softmax for each sample in the batch.

        :param x: Softmax output (batch_size, num_classes)
        :return: Jacobian matrix (batch_size, num_classes, num_classes)
        """
        batch_size, num_classes = x.shape
        jacobian_matrix = np.zeros((batch_size, num_classes, num_classes))

        for i in range(batch_size):
            s_i = x[i].reshape(-1, 1)
            jacobian_matrix[i] = np.diagflat(s_i) - np.dot(s_i, s_i.T)

        return jacobian_matrix




class Linear(ActivationFunction):
    def forward(self, x: np.ndarray) -> np.ndarray:
        return x

    def derivative(self, x: np.ndarray) -> np.ndarray:
        return np.ones_like(x)

class Softplus(ActivationFunction):
    def forward(self, x: np.ndarray) -> np.ndarray:
        return np.log(1 + np.exp(x))

    def derivative(self, x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-x))


class Mish(ActivationFunction):
    def forward(self, x: np.ndarray) -> np.ndarray:
        return x * np.tanh(np.log1p(np.exp(x)))

    def derivative(self, x: np.ndarray) -> np.ndarray:
        softplus_x = np.log1p(np.exp(x))
        tanh_softplus = np.tanh(softplus_x)
        return tanh_softplus + x * (1 - tanh_softplus ** 2) * (1 / (1 + np.exp(-x)))


class LossFunction(ABC):
    @abstractmethod
    def loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def derivative(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        pass


class SquaredError(LossFunction):
    def loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        return 1/2 * np.square(y_pred-y_true)

    def derivative(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        return (y_pred - y_true)/y_pred.shape[0]


class CrossEntropy(LossFunction):
    def loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:

        y_pred = np.clip(y_pred, 1e-15, 1 - 1e-15)
        return -np.mean(np.sum(y_true * np.log(y_pred), axis=1))

    def derivative(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:

        y_pred = np.clip(y_pred, 1e-15, 1 - 1e-15)
        return -y_true / y_pred

class BinaryCrossEntropy(LossFunction):
    def loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """
        Computes binary cross-entropy loss
        """
        y_pred = np.clip(y_pred, 1e-15, 1 - 1e-15)
        return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))

    def derivative(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """
        Computes gradient of binary cross-entropy loss
        """
        y_pred = np.clip(y_pred, 1e-15, 1 - 1e-15)
        return (y_pred - y_true) / (y_pred * (1 - y_pred) * len(y_true))





class Layer:
    def __init__(self, fan_in: int, fan_out: int, activation_function: ActivationFunction, dropout_rate=0.0):
        """
        Initializes a layer of neurons

        :param fan_in: number of neurons in previous (presynpatic) layer
        :param fan_out: number of neurons in this layer
        :param activation_function: instance of an ActivationFunction
        """
        self.fan_in = fan_in
        self.fan_out = fan_out
        self.activation_function = activation_function
        self.dropout_rate = dropout_rate


        #weight initilization


        # this will store the activations (forward prop)
        self.activations = None
        # this will store the delta term
        self.delta = None
        self.dropout_mask = None


        #changed this to glorot uniform initialization based on the submission requirement.. I used he initialization before that.


        self.W = np.random.uniform(-1, 1, (fan_in, fan_out)) * np.sqrt(6.0 / (fan_in + fan_out))
        #self.W = np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)

        self.b = np.zeros((fan_out,))

    def forward(self, h: np.ndarray, training = True):
        """
        Computes the activations for this layer

        :param h: input to layer
        :return: layer activations
        """
        #Z calculation

        Z = np.dot(h, self.W) + self.b
        #self.activations = None
        activations = self.activation_function.forward(Z)

        #storing activations



        if training and self.dropout_rate > 0:
            # Apply dropout mask
            self.dropout_mask = (np.random.rand(*activations.shape) > self.dropout_rate) / (1.0 - self.dropout_rate)
            activations *= self.dropout_mask
        else:
            self.dropout_mask = np.ones_like(activations)

        self.activations = activations
        return self.activations








    def backward(self, h: np.ndarray, delta: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
      """
      Apply backpropagation to this layer and return the weight and bias gradients.

      :param h: Input to this layer.
      :param delta: Delta term from the layer above.
      :return: (Weight gradients, Bias gradients).
      """
      if isinstance(self.activation_function, Softmax):

        # Compute the Softmax derivative using the Jacobian
        softmax_out = self.activations
        softmax_jacobian = self.activation_function.derivative(softmax_out)

        # Multiply Jacobian by delta
        dZ = np.einsum('bij,bj->bi', softmax_jacobian, delta)
      else:
        dZ = delta * self.activation_function.derivative(self.activations)


    #apply dropout mask
      if self.dropout_rate > 0 and self.dropout_mask is not None:
        dZ *= self.dropout_mask



    # Compute weight and bias gradients
      dL_dW = np.dot(h.T, dZ) / h.shape[0]
      dL_db = np.sum(dZ, axis=0, keepdims=True) / h.shape[0]

      self.delta = np.dot(dZ, self.W.T)

      return dL_dW, dL_db




class MultilayerPerceptron:
    def __init__(self, layers: Tuple[Layer]):
        """
        Create a multilayer perceptron (densely connected multilayer neural network)
        :param layers: list or Tuple of layers
        """
        self.layers = layers

    def forward(self, x: np.ndarray,training=True) -> np.ndarray:
        """
        This takes the network input and computes the network output (forward propagation)
        :param x: network input
        :return: network output
        """

        for layer in self.layers:
            x = layer.forward(x,training=training)
        return x

    def backward(self, loss_grad: np.ndarray, input_data: np.ndarray) -> Tuple[list, list]:
      """
      Applies backpropagation to compute gradients of weights and biases for all layers in the network.

      :param loss_grad: Gradient of loss w.r.t. final layer output (dL/dA).
      :param input_data: The input data to the network (train_x for the first layer).
      :return: (List of weight gradients for all layers, List of bias gradients for all layers).
      """

      dl_dw_all = []
      dl_db_all = []

      dL_dA = loss_grad

    # Iterate backward through layers
      for i in reversed(range(len(self.layers))):
        layer = self.layers[i]


        if i == 0:
            h = input_data
        else:
            h = self.layers[i - 1].activations

        # Compute backpropagation step for this layer
        dL_dW, dL_db = layer.backward(h, dL_dA)


        dl_dw_all.append(dL_dW)
        dl_db_all.append(dL_db)

        dL_dA = layer.delta

    # Reverse lists to match layer order
      dl_dw_all.reverse()
      dl_db_all.reverse()

      return dl_dw_all, dl_db_all






    def train(self, train_x: np.ndarray, train_y: np.ndarray, val_x: np.ndarray, val_y: np.ndarray, loss_func: LossFunction, learning_rate: float=1E-3, batch_size: int=16, epochs: int=32, model_type: str="classification",RMSProp: bool=False) -> Tuple[np.ndarray, np.ndarray]:
    #def train(self, train_x: np.ndarray, train_y: np.ndarray, val_x: np.ndarray, val_y: np.ndarray, loss_func: LossFunction, learning_rate: float=1E-3, batch_size: int=16, epochs: int=32,model_type:mod_type) -> Tuple[np.ndarray, np.ndarray]:
        """
        Train the multilayer perceptron

        :param train_x: full training set input of shape (n x d) n = number of samples, d = number of features
        :param train_y: full training set output of shape (n x q) n = number of samples, q = number of outputs per sample
        :param val_x: full validation set input
        :param val_y: full validation set output
        :param loss_func: instance of a LossFunction
        :param learning_rate: learning rate for parameter updates
        :param batch_size: size of each batch
        :param epochs: number of epochs
        :param model_type: type of the model(regression/classification)

        :return:
        """

        #initializing RMSProp parameters
        if RMSProp:
          self.beta = 0.9
          self.epsilon = 1e-8

          for layer in self.layers:
            layer.m_W = np.zeros_like(layer.W)
            layer.m_b = np.zeros_like(layer.b)



        training_losses = []
        validation_losses = []


        #define epoch loop

        for epoch in range(epochs):

          #define batch loop
          total_loss = 0

          for batch_x, batch_y in batch_generator(train_x, train_y, batch_size):


            #forward pass
            y_pred = self.forward(batch_x,training=True)

            #compute loss

            batchloss = loss_func.loss(batch_y, y_pred)

            if batchloss.ndim > 0:
              batchloss = np.mean(batchloss)


            total_loss = total_loss + batchloss

            #print(total_loss)



            dL_dW, dL_db  = self.backward(loss_func.derivative(batch_y[:len(y_pred)], y_pred), batch_x)


            #update weights
            max_grad_norm = 1.0


            for i in range(len(self.layers)):

                layer = self.layers[i]


                if RMSProp:
                  layer.m_W = self.beta * layer.m_W + (1 - self.beta) * (dL_dW[i] ** 2)
                  layer.m_b = self.beta * layer.m_b + (1 - self.beta) * (dL_db[i].squeeze() ** 2)

                  layer.W -= learning_rate * dL_dW[i] / (np.sqrt(layer.m_W) + self.epsilon)

                  layer.b -= learning_rate * dL_db[i].squeeze() / (np.sqrt(layer.m_b) + self.epsilon)

                else:

                  layer.W -= learning_rate * dL_dW[i]
                  layer.b -= learning_rate * dL_db[i].squeeze()









          num_batches = len(train_x) / batch_size

          training_losses.append(total_loss / num_batches)




          val_output = self.forward(val_x,training = False)
          val_loss = loss_func.loss(val_y, val_output)

          # Ensure val_loss is scalar
          validation_losses.append(np.mean(val_loss) if val_loss.ndim > 0 else val_loss)




          # Compute training accuracy at the end of the epoch based on the model type

          if model_type == 'classification':
            train_acc = compute_accuracy(self, train_x, train_y)
            val_acc = compute_accuracy(self, val_x, val_y)

            #print(f"{training_losses}")

            print(f"Epoch {epoch+1}/{epochs} - Training Loss: {training_losses[-1]:.4f} - Training Acc: {train_acc:.2f}% - Validation Acc: {val_acc:.2f}% - Validation Loss: {validation_losses[-1]:.4f}")

          else:
            # Compute regression metrics first
            train_mse, train_mae, train_r2 = compute_regression_metrics(self, train_x, train_y)
            val_mse, val_mae, val_r2 = compute_regression_metrics(self, val_x, val_y)


            train_mse = float(train_mse)
            train_mae = float(train_mae)
            train_r2 = float(train_r2)

            val_mse = float(val_mse)
            val_mae = float(val_mae)
            val_r2 = float(val_r2)

            print(f"Epoch {epoch+1}/{epochs} - Training MSE: {train_mse:.4f} - Validation MSE: {val_mse:.4f} - Training MAE: {train_mae:.4f} - Validation MAE: {val_mae:.4f} - Training R²: {train_r2:.4f} - Validation R²: {val_r2:.4f}")








        return training_losses, validation_losses


#helper functions

def compute_accuracy(model, X, y):
    y_pred = model.forward(X)
    if y.shape[1] > 1:
        y_pred_class = np.argmax(y_pred, axis=1)
        y_true_class = np.argmax(y, axis=1)
    else:
        y_pred_class = (y_pred > 0.5).astype(int)
        y_true_class = y.astype(int)

    return np.mean(y_pred_class == y_true_class) * 100



def compute_regression_metrics(model, X, y):
    """
    Compute evaluation metrics for regression tasks (MPG).

    :param model: Trained MLP model
    :param X: Input features (numpy array)
    :param y: True labels (numpy array)
    :return: MSE, MAE, R² Score (all as Python floats)
    """
    y_pred = model.forward(X)

    mse = np.mean((y - y_pred) ** 2)
    mae = np.mean(np.abs(y - y_pred))
    ss_total = np.sum((y - np.mean(y)) ** 2)
    ss_residual = np.sum((y - y_pred) ** 2)
    r2_score = 1 - (ss_residual / ss_total) if ss_total != 0 else 0


    # Convert values to floats if they are NumPy scalars
    return float(mse), float(mae), float(r2_score)