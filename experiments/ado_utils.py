"""
ado_utils.py

完整的 ADO (Adaptive Design Optimization) 工具函數

提供 ADO 實驗所需的核心功能，包括效用函數計算、貝葉斯更新、
收斂檢查、最佳設計選擇等功能。

Author: EJ  
Last reviewed: 2025-06
"""

import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any, List
from scipy.stats import entropy

# 設定日誌
logger = logging.getLogger(__name__)


class ADOEngine:
    """ADO 引擎類別，處理心理計量函數的適應性實驗設計"""
    
    def __init__(self, 
                 design_space: np.ndarray = None,
                 threshold_range: Tuple[float, float] = (10, 99),
                 slope_range: Tuple[float, float] = (0.1, 3.0),
                 threshold_points: int = 41,
                 slope_points: int = 30):
        """初始化 ADO 引擎
        
        Args:
            design_space: 設計空間（MTF 值）
            threshold_range: 閾值參數範圍
            slope_range: 斜率參數範圍  
            threshold_points: 閾值網格點數
            slope_points: 斜率網格點數
        """
        
        # 設計空間：可選的 MTF 值
        if design_space is None:
            self.design_space = np.arange(1, 100, 1)  # 1% 到 99%，每 1% 一步
        else:
            self.design_space = np.array(design_space)
        
        # 參數網格
        self.threshold_grid = np.linspace(threshold_range[0], threshold_range[1], threshold_points)
        self.slope_grid = np.linspace(slope_range[0], slope_range[1], slope_points)
        
        # 建立 2D 參數網格
        self.threshold_mesh, self.slope_mesh = np.meshgrid(self.threshold_grid, self.slope_grid)
        self.param_shape = self.threshold_mesh.shape
        
        # 初始化先驗分布（均勻分布）
        self.prior = np.ones(self.param_shape) / np.prod(self.param_shape)
        self.posterior = self.prior.copy()
        
        # 記錄實驗歷史
        self.trial_history = []
        self.response_history = []
        
        logger.info(f"ADO 引擎初始化完成：{len(self.design_space)} 個設計點，{np.prod(self.param_shape)} 個參數組合")
    
    
    def logistic_psychometric(self, mtf: float, threshold: float, slope: float) -> float:
        """心理計量函數 (Logistic)
        
        Args:
            mtf: MTF 刺激值 (%)
            threshold: 閾值參數
            slope: 斜率參數
            
        Returns:
            反應機率 (0-1)
        """
        try:
            z = slope * (mtf - threshold)
            # 數值穩定性處理
            z = np.clip(z, -700, 700)
            return 1.0 / (1.0 + np.exp(-z))
        except:
            return 0.5
    
    
    def calculate_likelihood(self, mtf: float, response: int) -> np.ndarray:
        """計算給定 MTF 和反應的似然函數
        
        Args:
            mtf: MTF 值
            response: 反應 (0 或 1)
            
        Returns:
            likelihood: 似然函數陣列
        """
        # 計算每個參數組合的預測機率
        prob_matrix = np.zeros(self.param_shape)
        
        for i in range(self.param_shape[0]):
            for j in range(self.param_shape[1]):
                threshold = self.threshold_mesh[i, j]
                slope = self.slope_mesh[i, j]
                prob = self.logistic_psychometric(mtf, threshold, slope)
                
                # 計算似然：P(response|parameters)
                if response == 1:
                    prob_matrix[i, j] = prob
                else:
                    prob_matrix[i, j] = 1 - prob
        
        return prob_matrix
    
    
    def calculate_mutual_information(self, mtf: float) -> float:
        """計算給定 MTF 值的互資訊
        
        Args:
            mtf: 候選 MTF 值
            
        Returns:
            mutual_information: 互資訊值
        """
        # 計算每個參數組合的預測機率
        prob_yes_given_params = np.zeros(self.param_shape)
        
        for i in range(self.param_shape[0]):
            for j in range(self.param_shape[1]):
                threshold = self.threshold_mesh[i, j]
                slope = self.slope_mesh[i, j]
                prob_yes_given_params[i, j] = self.logistic_psychometric(mtf, threshold, slope)
        
        # 計算邊際機率：P(response=1|mtf)
        prob_yes_marginal = np.sum(self.posterior * prob_yes_given_params)
        prob_no_marginal = 1 - prob_yes_marginal
        
        # 避免 log(0)
        prob_yes_marginal = np.clip(prob_yes_marginal, 1e-10, 1-1e-10)
        prob_no_marginal = np.clip(prob_no_marginal, 1e-10, 1-1e-10)
        
        # 計算互資訊的兩個分量
        mi_yes = 0
        mi_no = 0
        
        # 對於 response=1 的情況
        likelihood_yes = self.calculate_likelihood(mtf, 1)
        posterior_given_yes = self.posterior * likelihood_yes
        norm_yes = np.sum(posterior_given_yes)
        if norm_yes > 0:
            posterior_given_yes /= norm_yes  # 正規化
            
            # KL 散度：D(P(θ|y=1,x) || P(θ)) - 數值穩定版本
            # 只計算 posterior > 0 的部分
            valid_mask = (posterior_given_yes > 1e-10) & (self.posterior > 1e-10)
            if np.any(valid_mask):
                kl_yes = np.sum(posterior_given_yes[valid_mask] * 
                               np.log(posterior_given_yes[valid_mask] / self.posterior[valid_mask]))
                mi_yes = prob_yes_marginal * kl_yes
        
        # 對於 response=0 的情況
        likelihood_no = self.calculate_likelihood(mtf, 0)
        posterior_given_no = self.posterior * likelihood_no
        norm_no = np.sum(posterior_given_no)
        if norm_no > 0:
            posterior_given_no /= norm_no  # 正規化
            
            # KL 散度：D(P(θ|y=0,x) || P(θ)) - 數值穩定版本
            valid_mask = (posterior_given_no > 1e-10) & (self.posterior > 1e-10)
            if np.any(valid_mask):
                kl_no = np.sum(posterior_given_no[valid_mask] * 
                              np.log(posterior_given_no[valid_mask] / self.posterior[valid_mask]))
                mi_no = prob_no_marginal * kl_no
        
        return mi_yes + mi_no
    
    
    def get_optimal_design(self) -> float:
        """選擇最佳的 MTF 值
        
        Returns:
            optimal_mtf: 最佳 MTF 值
        """
        utilities = []
        
        for mtf in self.design_space:
            utility = self.calculate_mutual_information(mtf)
            utilities.append(utility)
        
        utilities = np.array(utilities)
        optimal_idx = np.argmax(utilities)
        optimal_mtf = self.design_space[optimal_idx]
        
        # 除錯輸出 - 顯示ADO決策過程
        top_5_indices = np.argsort(utilities)[-5:][::-1]  # 取前5名
        print(f"🎯 ADO決策 (試次 {len(self.trial_history)+1}):")
        for i, idx in enumerate(top_5_indices):
            marker = "★" if idx == optimal_idx else " "
            print(f"  {marker} MTF {self.design_space[idx]:2.0f}%: utility={utilities[idx]:.4f}")
        
        return float(optimal_mtf)
    
    
    def update_posterior(self, mtf: float, response: int):
        """根據觀察結果更新後驗分布
        
        Args:
            mtf: 使用的 MTF 值
            response: 觀察到的反應 (0 或 1)
        """
        # 計算似然函數
        likelihood = self.calculate_likelihood(mtf, response)
        
        # 貝葉斯更新：posterior ∝ prior × likelihood
        self.posterior = self.posterior * likelihood
        
        # 正規化
        self.posterior = normalize_posterior(self.posterior)
        
        # 記錄歷史
        self.trial_history.append(mtf)
        self.response_history.append(response)
        
        logger.info(f"更新後驗分布：MTF={mtf}, 反應={response}")
    
    
    def get_parameter_estimates(self) -> Dict[str, float]:
        """取得目前的參數估計
        
        Returns:
            estimates: 包含均值和標準差的字典
        """
        # 計算期望值
        threshold_mean = np.sum(self.posterior * self.threshold_mesh)
        slope_mean = np.sum(self.posterior * self.slope_mesh)
        
        # 計算變異數和標準差
        threshold_var = np.sum(self.posterior * (self.threshold_mesh - threshold_mean)**2)
        slope_var = np.sum(self.posterior * (self.slope_mesh - slope_mean)**2)
        
        threshold_sd = np.sqrt(threshold_var)
        slope_sd = np.sqrt(slope_var)
        
        return {
            'threshold_mean': threshold_mean,
            'threshold_sd': threshold_sd,
            'slope_mean': slope_mean,
            'slope_sd': slope_sd
        }
    
    
    def check_convergence(self, min_trials: int = 15, 
                         threshold_convergence: float = 5.0,
                         slope_convergence: float = 0.3) -> bool:
        """檢查參數估計是否收斂
        
        Args:
            min_trials: 最少試驗次數
            threshold_convergence: 閾值收斂標準（標準差）
            slope_convergence: 斜率收斂標準（標準差）
            
        Returns:
            converged: 是否收斂
        """
        if len(self.trial_history) < min_trials:
            return False
        
        estimates = self.get_parameter_estimates()
        
        threshold_converged = estimates['threshold_sd'] < threshold_convergence
        slope_converged = estimates['slope_sd'] < slope_convergence
        
        return threshold_converged and slope_converged
    
    
    def get_trial_summary(self) -> Dict[str, Any]:
        """取得目前試驗的摘要資訊
        
        Returns:
            summary: 試驗摘要
        """
        estimates = self.get_parameter_estimates()
        converged = self.check_convergence()
        
        return {
            'trial_count': len(self.trial_history),
            'converged': converged,
            **estimates
        }


def safe_log(x: np.ndarray, epsilon: float = 1e-10) -> np.ndarray:
    """數值穩定的對數函數
    
    Args:
        x: 輸入陣列
        epsilon: 最小值，避免 log(0)
        
    Returns:
        對數值
    """
    return np.log(np.clip(x, epsilon, 1.0 - epsilon))


def normalize_posterior(posterior: np.ndarray) -> np.ndarray:
    """正規化後驗分布
    
    Args:
        posterior: 未正規化的後驗分布
        
    Returns:
        正規化後的後驗分布
    """
    total = np.sum(posterior)
    if total == 0 or not np.isfinite(total):
        logger.warning("後驗分布總和無效，返回均勻分布")
        return np.ones_like(posterior) / np.prod(posterior.shape)
    return posterior / total


if __name__ == "__main__":
    """測試 ADO 引擎"""
    
    print("測試 ADO 引擎...")
    
    # 初始化引擎
    engine = ADOEngine()
    
    # 模擬幾個試驗
    print("\n模擬試驗...")
    true_threshold = 50.0
    true_slope = 1.5
    
    for trial in range(10):
        # 取得最佳設計
        optimal_mtf = engine.get_optimal_design()
        
        # 模擬反應（基於真實參數）
        true_prob = engine.logistic_psychometric(optimal_mtf, true_threshold, true_slope)
        response = 1 if np.random.rand() < true_prob else 0
        
        # 更新引擎
        engine.update_posterior(optimal_mtf, response)
        
        # 取得估計
        estimates = engine.get_parameter_estimates()
        summary = engine.get_trial_summary()
        
        print(f"試驗 {trial+1}: MTF={optimal_mtf:.1f}, 反應={response}, "
              f"閾值估計={estimates['threshold_mean']:.1f}±{estimates['threshold_sd']:.1f}, "
              f"收斂={summary['converged']}")
    
    print("\n✓ ADO 引擎測試完成")