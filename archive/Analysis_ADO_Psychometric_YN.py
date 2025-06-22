# Analysis_ADO_Psychometric_YN.py
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import norm
import pandas as pd

# 讀入資料
df = pd.read_csv('../data/MTF_ADO_001_20250610_183428.csv')  # 假設已儲存為 CSV
x = df['mtf_value'].to_numpy()
y = df['response'].to_numpy()

# 定義 logistic function 或 cumulative Gaussian
def logistic(x, alpha, beta, gamma=0.0, lambda_=0.02):
    """ 2AFC 用 psychometric function: logistic with lapse/guess rate """
    return gamma + (1 - gamma - lambda_) / (1 + np.exp(-(x - alpha) / beta))

def cum_gauss(x, mu, sigma, gamma=0.0, lambda_=0.02):
    """ cumulative Gaussian """
    return gamma + (1 - gamma - lambda_) * norm.cdf(x, loc=mu, scale=sigma)

# 擬合 logistic function
params_log, _ = curve_fit(logistic, x, y, p0=[np.median(x), 10])

# 擬合 cumulative Gaussian
params_gauss, _ = curve_fit(cum_gauss, x, y, p0=[np.median(x), 10])

# 建立平滑曲線資料
x_fit = np.linspace(min(x), max(x), 300)
y_fit_log = logistic(x_fit, *params_log)
y_fit_gauss = cum_gauss(x_fit, *params_gauss)

# 畫圖
plt.figure()
plt.scatter(x, y, alpha=0.5, label='Raw Data', color='black')
plt.plot(x_fit, y_fit_log, label='Logistic Fit', linewidth=2)
plt.plot(x_fit, y_fit_gauss, label='Gaussian Fit', linewidth=2, linestyle='--')
plt.xlabel('MTF Value')
plt.ylabel('P(Clear)')
plt.title('Psychometric Function Fit')
plt.legend()
plt.grid(True)
plt.show()

# 印出 threshold 結果
print(f'Logistic threshold (alpha): {params_log[0]:.2f}, slope (beta): {params_log[1]:.2f}')
print(f'Cumulative Gaussian threshold (mu): {params_gauss[0]:.2f}, sigma: {params_gauss[1]:.2f}')
