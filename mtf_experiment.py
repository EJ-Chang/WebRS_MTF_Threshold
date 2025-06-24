"""
MTF Experiment Manager for Streamlit Web Interface
Integrates MTF ADO testing into the existing web framework
"""

import numpy as np
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import base64
from io import BytesIO
from PIL import Image
import cv2
from config.settings import PRACTICE_TRIAL_LIMIT

# Import the ADO and MTF utilities with proper fallback handling
# Force use of real ADO engine from ado_utils.py
try:
    from experiments.ado_utils import ADOEngine
    print("✅ Successfully imported real ADOEngine from experiments.ado_utils")
    ADO_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"Primary ADO import failed: {e}")
    
    # Try alternative path for different environments
    try:
        import sys
        import os
        # Add current directory to path for Replit/alternative environments
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'experiments'))
        
        from ado_utils import ADOEngine
        print("✅ Successfully imported real ADOEngine from alternative path")
        ADO_ENGINE_AVAILABLE = True
    except ImportError as e2:
        print(f"❌ Alternative ADO import also failed: {e2}")
        print("❌ CRITICAL: Real ADO engine not available - experiment will not use true ADO!")
        ADO_ENGINE_AVAILABLE = False

# Import MTF utilities
try:
    from experiments.mtf_utils import apply_mtf_to_image, load_and_prepare_image
    MTF_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"MTF utilities not available: {e}")
    MTF_UTILS_AVAILABLE = False
    
    # Try alternative path
    try:
        from mtf_utils import apply_mtf_to_image, load_and_prepare_image
        MTF_UTILS_AVAILABLE = True
        print("✅ Loaded MTF utilities from alternative path")
    except ImportError as e2:
        print(f"Alternative MTF import also failed: {e2}")
        MTF_UTILS_AVAILABLE = False
    
# Only provide fallback implementations for MTF utilities if needed
if not MTF_UTILS_AVAILABLE:
    def apply_mtf_to_image(image, mtf_percent):
        """Fallback MTF implementation using simple Gaussian blur"""
        import cv2
        # Simple approximation: lower MTF = more blur
        sigma = (100 - mtf_percent) / 20.0  # Convert MTF% to blur amount
        return cv2.GaussianBlur(image, (0, 0), sigmaX=sigma, sigmaY=sigma)
    
    def load_and_prepare_image(path, use_right_half=True):
        """Fallback image loading with text image support"""
        import cv2
        import os
        img = cv2.imread(path)
        if img is not None:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if use_right_half:
                # Check image type for cropping strategy
                image_name = os.path.basename(path).lower()
                
                if 'stimuli_img' in image_name:
                    # Original stimuli_img: take right half (original behavior)
                    width = img_rgb.shape[1]
                    mid_point = width // 2
                    img_rgb = img_rgb[:, mid_point:]
                else:
                    # All other images (text_img, tw_newsimg, us_newsimg): take center portion
                    height, width = img_rgb.shape[:2]
                    target_width = width // 2  # Target width is half of original
                    
                    # Calculate center region boundaries
                    center_x = width // 2
                    start_x = center_x - target_width // 2
                    end_x = start_x + target_width
                    
                    # Ensure we don't go out of bounds
                    start_x = max(0, start_x)
                    end_x = min(width, end_x)
                    
                    img_rgb = img_rgb[:, start_x:end_x]
            return img_rgb
        return None

# Only create fallback ADO if real ADO is not available
# THIS SHOULD NOT HAPPEN - we want to force use of real ADO only
if not ADO_ENGINE_AVAILABLE:
    print("🚨 WARNING: Using fallback ADO instead of real ADO - this defeats the purpose!")
    print("🚨 Please ensure experiments/ado_utils.py is available and working correctly!")
    
    class ADOEngine:
        """FALLBACK ADO - NOT REAL ADO! This should not be used if real ADO is available."""
        def __init__(self, **kwargs):
            print("🚨 FALLBACK ADO ENGINE INITIALIZED - NOT USING REAL ADO!")
            self.design_space = kwargs.get('design_space', np.arange(10, 100, 5))
            self.trial_history = []
            self.response_history = []
            
        def get_optimal_design(self):
            """Simple fallback design selection - NOT REAL ADO"""
            if len(self.trial_history) == 0:
                return 60.0
            
            # Very simple step-up/step-down strategy
            last_response = self.response_history[-1] if self.response_history else 1
            last_mtf = self.trial_history[-1] if self.trial_history else 60.0
            
            if last_response == 1:  # Clear response, make it harder
                return max(10.0, last_mtf - 10.0)
            else:  # Not clear, make it easier
                return min(99.0, last_mtf + 10.0)
        
        def update_posterior(self, mtf, response):
            """Record response - NO REAL BAYESIAN UPDATE"""
            self.trial_history.append(mtf)
            self.response_history.append(response)
        
        def get_parameter_estimates(self):
            """Fake parameter estimates - NOT REAL ADO"""
            if len(self.trial_history) == 0:
                return {
                    'threshold_mean': 50.0,
                    'threshold_sd': 20.0,
                    'slope_mean': 1.0,
                    'slope_sd': 0.5
                }
            
            # Fake decreasing uncertainty over time
            uncertainty = max(2.0, 20.0 - len(self.trial_history) * 1.5)
            estimated_threshold = np.mean(self.trial_history) if self.trial_history else 50.0
            
            return {
                'threshold_mean': estimated_threshold,
                'threshold_sd': uncertainty,
                'slope_mean': 1.0,
                'slope_sd': 0.5
            }
        
        def get_entropy(self):
            """Fake entropy calculation"""
            estimates = self.get_parameter_estimates()
            return estimates['threshold_sd'] / 10.0  # Fake entropy
else:
    print("✅ Real ADO engine is available and will be used!")

class PreciseTimer:
    """精確時間測量類別，用於校正系統延遲和提供準確的RT測量"""
    
    def __init__(self):
        self.system_time_offset = self.calibrate_system_delay()
        self.render_time_offset = 0.02  # 估計渲染延遲約20ms
        self.baseline_rts = []
        self.current_session_offset = 0
        
    def calibrate_system_delay(self) -> float:
        """測量系統調用延遲"""
        delays = []
        for _ in range(5):
            start = time.time()
            # 模擬典型操作的延遲
            time.sleep(0.001)  # 1ms的模擬操作
            end = time.time()
            delays.append(end - start - 0.001)  # 減去sleep時間
        
        return np.median(delays) if delays else 0.005  # 預設5ms
    
    def get_precise_onset_time(self) -> float:
        """獲取精確的stimulus開始時間（考慮系統延遲）"""
        raw_time = time.time()
        corrected_time = raw_time + self.system_time_offset + self.render_time_offset
        return corrected_time
    
    def calculate_precise_rt(self, stimulus_onset: float, response_time: float) -> float:
        """計算精確的反應時間"""
        raw_rt = response_time - stimulus_onset
        
        # 應用當前session的校正
        corrected_rt = raw_rt - self.current_session_offset
        
        # 確保RT為正值且合理
        if corrected_rt < 0.05:  # 少於50ms的RT可能是誤觸
            corrected_rt = 0.05
        elif corrected_rt > 10.0:  # 超過10秒的RT可能是系統問題
            corrected_rt = 10.0
            
        return corrected_rt
    
    def update_baseline(self, new_rt: float):
        """動態更新時間基準"""
        self.baseline_rts.append(new_rt)
        
        # 每10個trials重新校正一次
        if len(self.baseline_rts) % 10 == 0:
            self.recalibrate_timing()
    
    def recalibrate_timing(self):
        """重新校正時間測量"""
        if len(self.baseline_rts) < 20:
            return
            
        recent_rts = self.baseline_rts[-20:]  # 最近20個trials
        
        # 檢測時間漂移
        first_half = recent_rts[:10]
        second_half = recent_rts[10:]
        
        drift = np.median(second_half) - np.median(first_half)
        
        if abs(drift) > 0.05:  # 如果漂移超過50ms
            self.current_session_offset += drift
            print(f"時間校正：檢測到{drift*1000:.1f}ms漂移，已自動校正")
    
    def filter_outliers(self, reaction_times: List[float]) -> List[float]:
        """過濾異常的反應時間"""
        if len(reaction_times) < 3:
            return reaction_times
            
        # 使用IQR方法過濾異常值
        q1, q3 = np.percentile(reaction_times, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # 過濾異常值
        clean_rts = [rt for rt in reaction_times 
                     if lower_bound <= rt <= upper_bound]
        
        return clean_rts if clean_rts else reaction_times

class StimulusCache:
    """刺激圖片緩存系統，用於預載和快速提供MTF圖片"""
    
    def __init__(self):
        self.cache = {}
        self.max_cache_size = 20  # 最多緩存20張圖片
        self.access_count = {}  # 記錄訪問次數，用於LRU
        
    def get_cache_key(self, mtf_value: float, image_hash: str = None) -> str:
        """生成緩存鍵值"""
        rounded_mtf = round(mtf_value, 1)  # 四捨五入到0.1精度
        return f"mtf_{rounded_mtf}_{image_hash or 'default'}"
    
    def put(self, mtf_value: float, image_data: str, image_hash: str = None):
        """將圖片存入緩存"""
        cache_key = self.get_cache_key(mtf_value, image_hash)
        
        # 如果緩存已滿，移除最少使用的項目
        if len(self.cache) >= self.max_cache_size:
            self._evict_lru()
        
        self.cache[cache_key] = {
            'data': image_data,
            'timestamp': time.time(),
            'mtf_value': mtf_value
        }
        self.access_count[cache_key] = 0
    
    def get(self, mtf_value: float, image_hash: str = None) -> Optional[str]:
        """從緩存獲取圖片"""
        cache_key = self.get_cache_key(mtf_value, image_hash)
        
        if cache_key in self.cache:
            self.access_count[cache_key] += 1
            return self.cache[cache_key]['data']
        
        return None
    
    def _evict_lru(self):
        """移除最少使用的緩存項目"""
        if not self.cache:
            return
            
        # 找到使用次數最少的項目
        lru_key = min(self.access_count.keys(), key=lambda k: self.access_count[k])
        
        del self.cache[lru_key]
        del self.access_count[lru_key]
    
    def preload_likely_mtf_values(self, base_image: np.ndarray, current_estimates: Dict):
        """根據當前ADO估計預載可能的MTF值"""
        if not current_estimates:
            return
            
        threshold_mean = current_estimates.get('threshold_mean', 50.0)
        threshold_sd = current_estimates.get('threshold_sd', 15.0)
        
        # 預測可能的下一個MTF值範圍
        likely_range = [
            max(10.0, threshold_mean - 2 * threshold_sd),
            min(99.0, threshold_mean + 2 * threshold_sd)
        ]
        
        # 在該範圍內生成幾個可能的MTF值
        candidate_mtf_values = np.linspace(likely_range[0], likely_range[1], 5)
        
        for mtf_value in candidate_mtf_values:
            cache_key = self.get_cache_key(mtf_value)
            if cache_key not in self.cache:
                # 在背景預先生成這些圖片
                try:
                    # 這裡會調用MTF處理函數
                    from experiments.mtf_utils import apply_mtf_to_image
                    processed_img = apply_mtf_to_image(base_image, mtf_value)
                    
                    # 轉換為base64
                    img_pil = Image.fromarray(processed_img)
                    buffer = BytesIO()
                    img_pil.save(buffer, format='PNG')
                    img_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    self.put(mtf_value, f"data:image/png;base64,{img_str}")
                except Exception as e:
                    print(f"預載MTF {mtf_value:.1f}失敗: {e}")

class MTFExperimentManager:
    """Manages MTF ADO experiment for web interface"""
    
    def __init__(self, 
                 max_trials: int = 50,
                 min_trials: int = 15,
                 convergence_threshold: float = 0.15,
                 participant_id: str = "",
                 base_image_path: str = None,
                 is_practice: bool = False):
        """
        Initialize MTF experiment manager
        
        Args:
            max_trials: Maximum number of trials
            min_trials: Minimum trials before convergence check
            convergence_threshold: Convergence criterion for threshold SD
            participant_id: Participant identifier
            base_image_path: Path to base stimulus image
            is_practice: Whether this is practice mode (uses same ADO logic, but limited trials)
        """
        # Practice mode setup: use same ADO logic but limit trials
        self.is_practice = is_practice
        if is_practice:
            # Practice mode: configurable trials, same ADO logic
            self.max_trials = PRACTICE_TRIAL_LIMIT
            self.min_trials = 1  # Allow convergence check after 1 trial in practice
        else:
            self.max_trials = max_trials
            self.min_trials = min_trials
            
        self.convergence_threshold = convergence_threshold
        self.participant_id = participant_id
        
        # Smart path resolution for different environments
        if base_image_path is None:
            # Auto-detect base image path
            possible_paths = [
                "stimuli_preparation/stimuli_img.png",
                "./stimuli_preparation/stimuli_img.png",
                os.path.join(os.path.dirname(__file__), "stimuli_preparation", "stimuli_img.png"),
                "stimuli_img.png"
            ]
            
            self.base_image_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    self.base_image_path = path
                    print(f"✅ Found base image at: {path}")
                    break
            
            if self.base_image_path is None:
                print("⚠️ Base image not found, will use generated test pattern")
                self.base_image_path = "test_pattern"
        else:
            # Validate that base_image_path is not None and is a valid path
            if base_image_path and isinstance(base_image_path, str):
                self.base_image_path = base_image_path
            else:
                print(f"⚠️ Invalid base_image_path provided: {base_image_path}, using auto-detection")
                # Fall back to auto-detection
                possible_paths = [
                    "stimuli_preparation/stimuli_img.png",
                    "./stimuli_preparation/stimuli_img.png",
                    os.path.join(os.path.dirname(__file__), "stimuli_preparation", "stimuli_img.png"),
                    "stimuli_img.png"
                ]
                
                self.base_image_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        self.base_image_path = path
                        print(f"✅ Found base image at: {path}")
                        break
                
                if self.base_image_path is None:
                    print("⚠️ Base image not found, will use generated test pattern")
                    self.base_image_path = "test_pattern"
        
        # Trial data storage
        self.trial_data = []
        # Remove internal counter - use session state instead
        # self.current_trial = 0  # REMOVED: Use session state counters
        self.converged = False
        
        # Initialize ADO engine
        self.ado_engine = None
        self.base_image = None
        
        # Initialize timing and caching systems
        self.precise_timer = PreciseTimer()
        self.stimulus_cache = StimulusCache()
        
        # Load base image
        self._load_base_image()
        self._initialize_ado_engine()
    
    def _load_base_image(self):
        """Load and prepare the base stimulus image"""
        try:
            if self.base_image_path == "test_pattern" or not os.path.exists(self.base_image_path):
                print("🎨 Creating test pattern (no base image found)")
                self.base_image = self._create_test_pattern()
            else:
                self.base_image = load_and_prepare_image(self.base_image_path, use_right_half=True)
                if self.base_image is not None:
                    print(f"✅ Base image loaded: {self.base_image.shape}")
                else:
                    print("⚠️ Failed to load base image, creating test pattern")
                    self.base_image = self._create_test_pattern()
        except Exception as e:
            print(f"⚠️ Error loading base image: {e}")
            print("🎨 Falling back to test pattern")
            self.base_image = self._create_test_pattern()
    
    def _create_test_pattern(self) -> np.ndarray:
        """Create a test pattern if base image is not available"""
        # Create a simple Gabor-like pattern for testing
        height, width = 400, 400
        y, x = np.ogrid[:height, :width]
        
        # Create sinusoidal grating
        frequency = 0.1
        pattern = np.sin(2 * np.pi * frequency * x) * np.cos(2 * np.pi * frequency * y)
        
        # Normalize to 0-255 range
        pattern = ((pattern + 1) * 127.5).astype(np.uint8)
        
        # Convert to RGB
        rgb_pattern = np.stack([pattern, pattern, pattern], axis=-1)
        
        return rgb_pattern
    
    def _initialize_ado_engine(self):
        """Initialize the ADO engine for MTF testing"""
        try:
            self.ado_engine = ADOEngine(
                design_space=np.arange(10, 100, 1),  # MTF values from 10% to 99%
                threshold_range=(5, 99),
                slope_range=(0.05, 5.0),
                threshold_points=31,
                slope_points=21
            )
            print("ADO engine initialized successfully")
        except Exception as e:
            print(f"Failed to initialize ADO engine: {e}")
            self.ado_engine = None
    
    def generate_stimulus_image(self, mtf_value: float) -> Optional[str]:
        """
        Generate stimulus image with specified MTF value
        Returns base64 encoded image for web display
        Uses caching for performance improvement
        """
        try:
            if self.base_image is None:
                print("⚠️ No base image available")
                return None
            
            # 首先檢查緩存
            cached_image = self.stimulus_cache.get(mtf_value)
            if cached_image:
                return cached_image
                
            # 如果沒有緩存，即時生成
            img_mtf = apply_mtf_to_image(self.base_image, mtf_value)
            
            if img_mtf is None:
                print("⚠️ Warning: apply_mtf_to_image returned None")
                return None
            
            # Convert to PIL Image
            img_pil = Image.fromarray(img_mtf)
            
            # Convert to base64 for web display
            buffer = BytesIO()
            img_pil.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            image_data = f"data:image/png;base64,{img_str}"
            
            # 存入緩存供未來使用
            self.stimulus_cache.put(mtf_value, image_data)
            
            return image_data
            
        except Exception as e:
            print(f"⚠️ Error generating stimulus: {e}")
            return None
    
    def get_next_trial(self) -> Optional[Dict]:
        """Get the next trial parameters using ADO"""
        # Import here to avoid circular dependency
        import streamlit as st
        
        # ADO convergence has been disabled to ensure timing accuracy
        # Only check trial count to ensure all max_trials are executed
        # Use session state counters instead of internal counter for synchronization
        
        # In practice mode, check practice trials completed
        if st.session_state.get('is_practice', False):
            practice_completed = st.session_state.get('practice_trials_completed', 0)
            if practice_completed >= PRACTICE_TRIAL_LIMIT:  # Practice limit: configurable trials
                return None
        else:
            # In experiment mode, check experiment trials completed
            experiment_trials = st.session_state.get('experiment_trial', 0)
            if experiment_trials >= self.max_trials:
                return None
        
        if self.ado_engine is None:
            # Fallback: random MTF selection
            mtf_value = float(np.random.choice(np.arange(10, 90, 10)))
        else:
            try:
                mtf_value = self.ado_engine.get_optimal_design()
            except Exception as e:
                print(f"ADO error: {e}")
                mtf_value = float(np.random.choice(np.arange(10, 90, 10)))
        
        # Remove internal counter increment - let session state handle this
        # self.current_trial += 1  # REMOVED: Session state will handle counter increment
        
        # Generate stimulus image
        stimulus_image = self.generate_stimulus_image(mtf_value)
        
        if stimulus_image is None:
            print(f"⚠️ Failed to generate stimulus image for MTF {mtf_value:.1f}%")
        
        # 在背景預載可能的下一個MTF值
        current_estimates = self.get_current_estimates()
        if current_estimates and self.base_image is not None:
            try:
                self.stimulus_cache.preload_likely_mtf_values(self.base_image, current_estimates)
            except Exception as e:
                print(f"Preloading error: {e}")
        
        # Get stimulus image name for recording
        stimulus_image_name = "unknown"
        if self.base_image_path and self.base_image_path != "test_pattern":
            stimulus_image_name = os.path.basename(self.base_image_path)
        elif self.base_image_path == "test_pattern":
            stimulus_image_name = "test_pattern"
        
        # Get trial number from session state for consistency
        import streamlit as st
        if st.session_state.get('is_practice', False):
            trial_number = st.session_state.get('practice_trials_completed', 0) + 1
        else:
            trial_number = st.session_state.get('experiment_trial', 0) + 1
        
        trial_data = {
            'trial_number': trial_number,
            'mtf_value': mtf_value,
            'stimulus_image': stimulus_image,
            'stimulus_image_file': stimulus_image_name,  # 記錄使用的圖片檔名
            'timestamp': datetime.now().isoformat(),
            'precise_onset_time': None  # 會在顯示時設定
        }
        
        return trial_data
    
    def record_response(self, trial_data: Dict, response: bool, reaction_time: float, 
                      stimulus_onset_time: float = None):
        """
        Record participant response and update ADO
        
        Args:
            trial_data: Current trial information
            response: True for "clear", False for "not clear"
            reaction_time: Raw response time in seconds
            stimulus_onset_time: Precise stimulus onset time
        """
        # Convert response to int (1 for clear, 0 for not clear)
        response_value = 1 if response else 0
        
        # 使用精確時間測量計算RT
        if stimulus_onset_time:
            precise_rt = self.precise_timer.calculate_precise_rt(
                stimulus_onset_time, 
                stimulus_onset_time + reaction_time
            )
            # 更新時間基準
            self.precise_timer.update_baseline(precise_rt)
        else:
            precise_rt = reaction_time
        
        # Update ADO engine
        if self.ado_engine:
            try:
                self.ado_engine.update_posterior(trial_data['mtf_value'], response_value)
                estimates = self.ado_engine.get_parameter_estimates()
                
                # Check convergence using session state or trial data length
                # Import here to avoid circular dependency
                import streamlit as st
                
                # Get trial count from session state or fallback to trial data length
                if st.session_state.get('is_practice', False):
                    completed_trials = st.session_state.get('practice_trials_completed', 0)
                else:
                    completed_trials = st.session_state.get('experiment_trial', 0)
                
                # Fallback to trial data length if session state unavailable
                if completed_trials == 0:
                    completed_trials = len(self.trial_data)
                
                if completed_trials >= self.min_trials:
                    self.converged = estimates['threshold_sd'] < self.convergence_threshold
                
            except Exception as e:
                print(f"ADO update error: {e}")
                estimates = {
                    'threshold_mean': np.nan,
                    'threshold_sd': np.nan,
                    'slope_mean': np.nan,
                    'slope_sd': np.nan
                }
        else:
            estimates = {
                'threshold_mean': np.nan,
                'threshold_sd': np.nan,
                'slope_mean': np.nan,
                'slope_sd': np.nan
            }
        
        # Store trial result
        trial_result = {
            **trial_data,
            'response': response_value,
            'response_text': 'clear' if response else 'not_clear',
            'reaction_time': reaction_time,
            'precise_reaction_time': precise_rt,  # 精確RT
            'threshold_mean': estimates['threshold_mean'],
            'threshold_sd': estimates['threshold_sd'],
            'slope_mean': estimates['slope_mean'],
            'slope_sd': estimates['slope_sd'],
            'converged': self.converged
        }
        
        self.trial_data.append(trial_result)
        
        return trial_result
    
    def get_current_estimates(self) -> Dict:
        """Get current parameter estimates from ADO"""
        if self.ado_engine and len(self.trial_data) > 0:
            try:
                return self.ado_engine.get_parameter_estimates()
            except:
                pass
        
        return {
            'threshold_mean': np.nan,
            'threshold_sd': np.nan,
            'slope_mean': np.nan,
            'slope_sd': np.nan
        }
    
    def is_experiment_complete(self) -> bool:
        """Check if experiment should end"""
        # Import here to avoid circular dependency
        import streamlit as st
        
        # ADO convergence has been disabled to ensure timing accuracy
        # Only check trial count to ensure all max_trials are executed
        # Use session state counters for synchronization
        
        # In practice mode, never consider "complete" - let session manager handle this
        if st.session_state.get('is_practice', False):
            return False  # Practice completion is handled by session manager
        else:
            # In experiment mode, check if we've reached max trials
            experiment_trials = st.session_state.get('experiment_trial', 0)
            return experiment_trials >= self.max_trials
    
    def get_experiment_summary(self) -> Dict:
        """Get experiment summary statistics"""
        if not self.trial_data:
            return {}
        
        # Calculate basic statistics
        total_trials = len(self.trial_data)
        clear_responses = sum(1 for trial in self.trial_data if trial['response'] == 1)
        accuracy_rate = clear_responses / total_trials if total_trials > 0 else 0
        
        reaction_times = [trial['reaction_time'] for trial in self.trial_data]
        avg_rt = np.mean(reaction_times) if reaction_times else 0
        
        # Get final estimates
        final_estimates = self.get_current_estimates()
        
        # Get stimulus image name for summary
        stimulus_image_name = "unknown"
        if self.base_image_path and self.base_image_path != "test_pattern":
            stimulus_image_name = os.path.basename(self.base_image_path)
        elif self.base_image_path == "test_pattern":
            stimulus_image_name = "test_pattern"
        
        return {
            'total_trials': total_trials,
            'clear_responses': clear_responses,
            'accuracy_rate': accuracy_rate,
            'average_reaction_time': avg_rt,
            'converged': self.converged,
            'final_threshold': final_estimates.get('threshold_mean', np.nan),
            'threshold_uncertainty': final_estimates.get('threshold_sd', np.nan),
            'participant_id': self.participant_id,
            'stimulus_image_file': stimulus_image_name  # 記錄使用的圖片檔名
        }
    
    def get_ado_entropy(self) -> float:
        """Get current ADO entropy (uncertainty measure)"""
        if self.ado_engine and hasattr(self.ado_engine, 'get_entropy'):
            try:
                return self.ado_engine.get_entropy()
            except Exception as e:
                print(f"Error getting ADO entropy: {e}")
                return float('nan')
        elif self.ado_engine and hasattr(self.ado_engine, 'get_parameter_estimates'):
            # Fallback: use threshold SD as entropy proxy
            try:
                estimates = self.ado_engine.get_parameter_estimates()
                threshold_sd = estimates.get('threshold_sd', 20.0)
                # Convert SD to entropy-like measure (higher SD = higher entropy)
                entropy = np.log(1 + threshold_sd)
                return entropy
            except Exception as e:
                print(f"Error calculating entropy from SD: {e}")
                return float('nan')
        else:
            return float('nan')
    
    def export_data(self) -> List[Dict]:
        """Export trial data for analysis"""
        return self.trial_data.copy()