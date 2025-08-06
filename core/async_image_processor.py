"""
Asynchronous image processor for pre-computing MTF stimuli during fixation periods.
"""
import threading
import time
import queue
from typing import Optional, Dict, Any
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

class AsyncImageProcessor:
    """Handles asynchronous pre-computation of MTF stimulus images during fixation periods"""
    
    def __init__(self):
        """Initialize the async image processor"""
        self.processing_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker_thread = None
        self.is_running = False
        self.current_task = None
        logger.debug("AsyncImageProcessor initialized")
    
    def start_processor(self):
        """Start the background processing thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_worker, daemon=True)
        self.worker_thread.start()
        logger.info("🔄 Async image processor started")
    
    def stop_processor(self):
        """Stop the background processing thread"""
        self.is_running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
        logger.info("⏹️ Async image processor stopped")
    
    def queue_image_generation(self, mtf_experiment_manager, next_mtf_value: float, task_id: str):
        """
        Queue an image generation task to be processed during fixation
        
        Args:
            mtf_experiment_manager: The MTF experiment manager instance
            next_mtf_value: MTF value for the next stimulus
            task_id: Unique identifier for this task
        """
        try:
            if not self.is_running:
                self.start_processor()
            
            task = {
                'type': 'generate_image',
                'mtf_experiment_manager': mtf_experiment_manager,
                'mtf_value': next_mtf_value,
                'task_id': task_id,
                'timestamp': time.time()
            }
            
            self.processing_queue.put(task)
            self.current_task = task_id
            logger.info(f"🎯 排隊生成 MTF {next_mtf_value:.1f}% 圖片 (任務 ID: {task_id})")
            
        except Exception as e:
            logger.error(f"Error queuing image generation: {e}")
    
    def get_processed_image(self, task_id: str, timeout: float = 0.1) -> Optional[np.ndarray]:
        """
        Get a processed image if available
        
        Args:
            task_id: Task identifier to retrieve
            timeout: Maximum time to wait for result
            
        Returns:
            Processed image array or None if not ready
        """
        try:
            # Check for completed results
            while not self.result_queue.empty():
                result = self.result_queue.get_nowait()
                if result['task_id'] == task_id:
                    if result['success']:
                        logger.info(f"✅ 異步生成完成 MTF {result['mtf_value']:.1f}% (任務 {task_id})")
                        return result['image']
                    else:
                        logger.error(f"❌ 異步生成失敗 (任務 {task_id}): {result.get('error')}")
                        return None
            
            return None
            
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Error getting processed image: {e}")
            return None
    
    def is_task_processing(self, task_id: str) -> bool:
        """
        Check if a specific task is currently being processed
        
        Args:
            task_id: Task identifier to check
            
        Returns:
            True if task is being processed
        """
        return self.current_task == task_id
    
    def _process_worker(self):
        """Background worker thread for processing images"""
        logger.info("🔄 Async image processor worker started")
        
        while self.is_running:
            try:
                # Get next task from queue (blocking with timeout)
                try:
                    task = self.processing_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                if task['type'] == 'generate_image':
                    self._process_image_generation(task)
                
                self.processing_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in async processor worker: {e}")
        
        logger.info("🔄 Async image processor worker stopped")
    
    def _process_image_generation(self, task: Dict[str, Any]):
        """
        Process an image generation task
        
        Args:
            task: Task dictionary containing generation parameters
        """
        start_time = time.time()
        task_id = task['task_id']
        mtf_value = task['mtf_value']
        
        try:
            # Set current task
            self.current_task = task_id
            
            # Generate the image using the MTF experiment manager
            mtf_experiment_manager = task['mtf_experiment_manager']
            
            logger.info(f"🎯 開始異步生成 MTF {mtf_value:.1f}% 圖片 (任務 {task_id})")
            
            # Use the generate_stimulus_image method
            stimulus_image = mtf_experiment_manager.generate_stimulus_image(mtf_value)
            
            processing_time = time.time() - start_time
            
            if stimulus_image is not None:
                result = {
                    'task_id': task_id,
                    'mtf_value': mtf_value,
                    'image': stimulus_image,
                    'success': True,
                    'processing_time': processing_time,
                    'timestamp': time.time()
                }
                logger.info(f"✅ 異步生成完成 MTF {mtf_value:.1f}% (用時 {processing_time:.3f}s)")
            else:
                result = {
                    'task_id': task_id,
                    'mtf_value': mtf_value,
                    'image': None,
                    'success': False,
                    'error': 'generate_stimulus_image returned None',
                    'processing_time': processing_time,
                    'timestamp': time.time()
                }
                logger.warning(f"❌ 異步生成失敗 MTF {mtf_value:.1f}% (用時 {processing_time:.3f}s)")
            
            # Put result in result queue
            self.result_queue.put(result)
            
        except Exception as e:
            processing_time = time.time() - start_time
            result = {
                'task_id': task_id,
                'mtf_value': mtf_value,
                'image': None,
                'success': False,
                'error': str(e),
                'processing_time': processing_time,
                'timestamp': time.time()
            }
            self.result_queue.put(result)
            logger.error(f"❌ 異步生成異常 MTF {mtf_value:.1f}%: {e} (用時 {processing_time:.3f}s)")
        
        finally:
            # Clear current task
            if self.current_task == task_id:
                self.current_task = None

# Global instance for the async processor
_async_processor = None

def get_async_processor() -> AsyncImageProcessor:
    """Get the global async image processor instance"""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncImageProcessor()
    return _async_processor

def cleanup_async_processor():
    """Clean up the global async processor"""
    global _async_processor
    if _async_processor is not None:
        _async_processor.stop_processor()
        _async_processor = None