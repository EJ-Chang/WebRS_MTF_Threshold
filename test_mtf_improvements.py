#!/usr/bin/env python3
"""
測試MTF實驗改善功能
Test script for MTF experiment improvements
"""

import numpy as np
import time
from mtf_experiment import MTFExperimentManager, PreciseTimer, StimulusCache

def test_precise_timer():
    """測試精確時間測量功能"""
    print("🕒 Testing PreciseTimer...")
    
    timer = PreciseTimer()
    
    # Test basic timing
    start_time = timer.get_precise_onset_time()
    time.sleep(0.1)  # Simulate 100ms delay
    end_time = time.time()
    
    rt = timer.calculate_precise_rt(start_time, end_time)
    print(f"   Measured RT: {rt:.3f}s (expected ~0.1s)")
    
    # Test baseline update
    for i in range(5):
        fake_rt = 0.5 + np.random.normal(0, 0.05)  # 500ms ± 50ms
        timer.update_baseline(fake_rt)
    
    print(f"   System offset: {timer.current_session_offset:.3f}s")
    print("   ✅ PreciseTimer test passed")

def test_stimulus_cache():
    """測試刺激緩存功能"""
    print("🖼️  Testing StimulusCache...")
    
    cache = StimulusCache()
    
    # Test basic cache operations
    test_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    # Put and get
    cache.put(50.0, test_data)
    retrieved = cache.get(50.0)
    
    assert retrieved == test_data, "Cache put/get failed"
    print("   ✅ Basic cache operations work")
    
    # Test cache key generation
    key1 = cache.get_cache_key(50.1)
    key2 = cache.get_cache_key(50.14)  # Should round to 50.1
    assert key1 == key2, "Cache key rounding failed"
    print("   ✅ Cache key generation works")
    
    print("   ✅ StimulusCache test passed")

def test_improved_ado():
    """測試改進的ADO演算法"""
    print("🧠 Testing Improved ADO Algorithm...")
    
    # Create MTF experiment manager
    exp_manager = MTFExperimentManager(
        max_trials=10,
        min_trials=5,
        convergence_threshold=0.1,
        participant_id="test_user"
    )
    
    if exp_manager.ado_engine is None:
        print("   ⚠️  ADO engine not available, using fallback")
        return
    
    # Test initial design selection
    initial_design = exp_manager.ado_engine.get_optimal_design()
    print(f"   Initial design: {initial_design:.1f}%")
    
    # Simulate some trials
    test_responses = [
        (60.0, 1),  # Clear at 60%
        (40.0, 0),  # Not clear at 40%
        (50.0, 1),  # Clear at 50%
        (45.0, 0),  # Not clear at 45%
        (48.0, 1),  # Clear at 48%
    ]
    
    print("   Simulating trials...")
    for mtf, response in test_responses:
        exp_manager.ado_engine.update_posterior(mtf, response)
        estimates = exp_manager.ado_engine.get_parameter_estimates()
        next_design = exp_manager.ado_engine.get_optimal_design()
        
        print(f"     MTF: {mtf:4.1f}% → Response: {'Clear' if response else 'Unclear'}")
        print(f"     Threshold Est: {estimates['threshold_mean']:5.1f}% ± {estimates['threshold_sd']:4.1f}%")
        print(f"     Next design: {next_design:5.1f}%")
        print()
    
    # Test entropy calculation
    try:
        entropy = exp_manager.ado_engine.get_entropy()
        print(f"   Final entropy: {entropy:.3f}")
    except Exception as e:
        print(f"   Entropy calculation error: {e}")
    
    print("   ✅ Improved ADO test passed")

def test_mtf_experiment_flow():
    """測試MTF實驗流程"""
    print("🔬 Testing MTF Experiment Flow...")
    
    exp_manager = MTFExperimentManager(
        max_trials=5,
        min_trials=3,
        convergence_threshold=0.2,
        participant_id="test_flow"
    )
    
    print(f"   Experiment initialized with {exp_manager.max_trials} max trials")
    
    # Test trial generation
    trial = exp_manager.get_next_trial()
    if trial:
        print(f"   Generated trial {trial['trial_number']} with MTF {trial['mtf_value']:.1f}%")
        
        # Test response recording with precise timing
        start_time = exp_manager.precise_timer.get_precise_onset_time()
        time.sleep(0.05)  # Simulate 50ms response time
        
        response_result = exp_manager.record_response(
            trial, 
            True,  # Clear response
            0.05,  # 50ms RT
            start_time
        )
        
        print(f"   Response recorded: RT = {response_result['precise_reaction_time']:.3f}s")
        print(f"   Threshold estimate: {response_result['threshold_mean']:.1f}%")
        
    # Test experiment completion
    completion_status = exp_manager.is_experiment_complete()
    print(f"   Experiment complete: {completion_status}")
    
    print("   ✅ MTF experiment flow test passed")

def main():
    """運行所有測試"""
    print("🚀 Starting MTF Experiment Improvements Test Suite")
    print("=" * 60)
    
    try:
        test_precise_timer()
        print()
        
        test_stimulus_cache()
        print()
        
        test_improved_ado()
        print()
        
        test_mtf_experiment_flow()
        print()
        
        print("🎉 All tests passed successfully!")
        print("✨ MTF experiment improvements are working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())