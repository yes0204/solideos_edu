"""
GPU 정보 수집기
NVIDIA GPU 모니터링
"""

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


def get_gpu_info():
    """GPU 정보 수집 (NVIDIA만 지원)"""
    if not GPU_AVAILABLE:
        return {'available': False, 'gpus': [], 'error': 'GPUtil not installed'}
    
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return {'available': False, 'gpus': [], 'error': 'No NVIDIA GPU found'}
        
        gpu_list = []
        for gpu in gpus:
            gpu_list.append({
                'id': gpu.id,
                'name': gpu.name,
                'load': gpu.load * 100,  # GPU 사용률 (%)
                'memory_total': gpu.memoryTotal,  # MB
                'memory_used': gpu.memoryUsed,  # MB
                'memory_free': gpu.memoryFree,  # MB
                'memory_percent': (gpu.memoryUsed / gpu.memoryTotal * 100) if gpu.memoryTotal > 0 else 0,
                'temperature': gpu.temperature,  # 섭씨
                'uuid': gpu.uuid
            })
        
        return {
            'available': True,
            'gpus': gpu_list,
            'error': None
        }
    except Exception as e:
        return {'available': False, 'gpus': [], 'error': str(e)}


def get_gpu_summary():
    """GPU 요약 정보"""
    info = get_gpu_info()
    if not info['available'] or not info['gpus']:
        return None
    
    # 첫 번째 GPU 정보 반환
    gpu = info['gpus'][0]
    return {
        'name': gpu['name'],
        'usage_percent': gpu['load'],
        'memory_percent': gpu['memory_percent'],
        'temperature': gpu['temperature']
    }
