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

# AND Logic Function
def AND_Logic_Function(x):
    w = np.array([1, 1])
    b = -1.5
    return perceptronModel(x, w, b)

# Testing the Perceptron Model
test1 = np.array([0, 1])
test2 = np.array([1, 1])
test3 = np.array([0, 0])
test4 = np.array([1, 0])

print("\tAND Function\t")
print("AND({}, {}) = {}".format(0, 1, AND_Logic_Function(test1)))
print("AND({}, {}) = {}".format(1, 1, AND_Logic_Function(test2)))
print("AND({}, {}) = {}".format(0, 0, AND_Logic_Function(test3)))
print("AND({}, {}) = {}".format(1, 0, AND_Logic_Function(test4)))
