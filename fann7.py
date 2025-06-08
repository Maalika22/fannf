import numpy as np 
import matplotlib.pyplot as plt 
from sklearn.datasets import make_classification 
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import Perceptron 
from sklearn.metrics import accuracy_score 

# Generate linearly separable data 
X, y = make_classification(
    n_samples=100,
    n_features=2,
    n_classes=2,
    n_clusters_per_class=1,
    n_redundant=0,
    n_informative=2,
    class_sep=1.5,
    random_state=42
) 

# Split the data into training and testing sets 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42) 

# Initialize and train the perceptron model 
perceptron = Perceptron() 
perceptron.fit(X_train, y_train) 

# Make predictions and calculate accuracy 
y_pred = perceptron.predict(X_test) 
accuracy = accuracy_score(y_test, y_pred) 
print(f'Test Accuracy: {accuracy}') 

# Plot the decision boundary 
x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1 
y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1 
xx, yy = np.meshgrid(
    np.arange(x_min, x_max, 0.02),
    np.arange(y_min, y_max, 0.02)
) 

Z = perceptron.predict(np.c_[xx.ravel(), yy.ravel()]) 
Z = Z.reshape(xx.shape) 

plt.contourf(xx, yy, Z, alpha=0.8) 
plt.scatter(X[:, 0], X[:, 1], c=y, marker='o', edgecolors='k') 
plt.title('Perceptron Decision Boundary') 
plt.xlabel('Feature 1') 
plt.ylabel('Feature 2') 
plt.show()
