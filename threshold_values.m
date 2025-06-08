disp('Enter weights');
w1 = input('Weight w1 = ');
w2 = input('Weight w2 = ');

disp('Enter Threshold Value');
theta = input('Theta = ');

% Input patterns
x1 = [0 0 1 1];
x2 = [0 1 0 1];

% Desired output for AND-NOT (x1 AND NOT x2)
z = [0 0 1 0];
y = [0 0 0 0];

con = 1;

while con
    zin = x1 * w1 + x2 * w2;

    for i = 1:4
        if zin(i) >= theta
            y(i) = 1;
        else
            y(i) = 0;
        end
    end

    disp('Output of Net:');
    disp(y);

    if isequal(y, z)
        con = 0;
    else
        disp('Net is not learning. Enter another set of weights and Threshold value.');
        w1 = input('Weight w1 = ');
        w2 = input('Weight w2 = ');
        theta = input('Theta = ');
    end
end

disp('McCulloch-Pitts Net for AND-NOT Function');
disp('Weights of Neuron:');
disp(w1);
disp(w2);
disp('Threshold Value:');
disp(theta);
