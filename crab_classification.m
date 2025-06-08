clc;
clear;
close all;
%% Step 1: Load the Dataset
data = readmatrix('crab_data.csv');  % Load CSV file

% Separate features and labels
X = data(:, 1:end-1)';        % Transpose to shape: features x samples
labels = data(:, end)';       % Class labels row vector

%% Step 2: Convert Labels to One-Hot
T = full(ind2vec(labels));    % Convert labels to one-hot format

%% Step 3: Create Pattern Recognition Network
net = patternnet(10);         % 10 hidden neurons (adjustable)

% Divide dataset: 70% train, 15% val, 15% test
net.divideParam.trainRatio = 0.7;
net.divideParam.valRatio = 0.15;
net.divideParam.testRatio = 0.15;

%% Step 4: Train the Network
[net, tr] = train(net, X, T);

%% Step 5: Test and Evaluate
Y = net(X);                   % Get predicted output
predicted = vec2ind(Y);       % Convert from one-hot to class index
actual = vec2ind(T);          % Actual class labels

accuracy = sum(predicted == actual) / numel(actual) * 100;
fprintf('Overall Accuracy: %.2f%%\n', accuracy);

%% Step 6: Plot Results
figure;
plotconfusion(T, Y);          % Confusion matrix

figure;
plotperform(tr);              % Performance plot

%% Optional: Save the model
save('trained_crab_net.mat', 'net');
