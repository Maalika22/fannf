x = -5:0.1:5;
tmp = exp(-x);
y1 = 1./(1 + tmp);                       % Logistic function
y2 = (1 - tmp) ./ (1 + tmp);             % Hyperbolic tangent function
y3 = x;                                  % Identity function

subplot(1,3,1);
plot(x, y1); grid on;
title('Logistic Function');
xlabel('x'); ylabel('y');
axis([-5 5 -2 2]); axis square;

subplot(1,3,2);
plot(x, y2); grid on;
title('Hyperbolic Tangent Function');
xlabel('x'); ylabel('y');
axis([-5 5 -2 2]); axis square;

subplot(1,3,3);
plot(x, y3); grid on;
title('Identity Function');
xlabel('x'); ylabel('y');
axis([-5 5 -5 5]); axis square;
