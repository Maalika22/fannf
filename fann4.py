# Importing Python library
import numpy as np

# Define Unit Step Function
def unitStep(v):
    if v >= 0:
        return 1
    else:
        return 0

# Design Perceptron Model
def perceptronModel(x, w, b):
    v = np.dot(w, x) + b
    y = unitStep(v)
    return y

# NOT Logic Function
def NOT_logicFunction(x):
    w = np.array([-1])
    b = 0.5
    return perceptronModel(x, w, b)

# Testing the Perceptron Model for NOT
print("\tNOT Function\t")
test1 = np.array([1])
test2 = np.array([0])

print("NOT({}) = {}".format(1, NOT_logicFunction(test1)))
print("NOT({}) = {}".format(0, NOT_logicFunction(test2)))
