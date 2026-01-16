"""
시스템 정보 수집기
CPU, 메모리, 디스크, 네트워크 모니터링
"""

import psutil
import platform
import time
from datetime import datetime


def get_cpu_info():
    """CPU 정보 수집"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
    cpu_freq = psutil.cpu_freq()
    cpu_count = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)
    
    return {
        'usage_percent': cpu_percent,
        'per_core': cpu_per_core,
        'frequency_current': cpu_freq.current if cpu_freq else 0,
        'frequency_max': cpu_freq.max if cpu_freq else 0,
        'frequency_min': cpu_freq.min if cpu_freq else 0,
        'cores_logical': cpu_count,
        'cores_physical': cpu_count_physical
    }


def get_memory_info():
    """메모리 정보 수집"""
    virtual = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        'total': virtual.total,
        'available': virtual.available,
        'used': virtual.used,
        'percent': virtual.percent,
        'swap_total': swap.total,
        'swap_used': swap.used,
        'swap_percent': swap.percent
    }


def get_disk_info():
    """디스크 정보 수집"""
    partitions = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            partitions.append({
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'fstype': partition.fstype,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent
            })
        except PermissionError:
            continue
    
    # 디스크 I/O
    io_counters = psutil.disk_io_counters()
    io_info = {
        'read_bytes': io_counters.read_bytes if io_counters else 0,
        'write_bytes': io_counters.write_bytes if io_counters else 0,
        'read_count': io_counters.read_count if io_counters else 0,
        'write_count': io_counters.write_count if io_counters else 0
    }
    
    return {
        'partitions': partitions,
        'io': io_info
    }


def get_network_info():
    """네트워크 정보 수집"""
    net_io = psutil.net_io_counters()
    
    # 인터페이스별 정보
    interfaces = {}
    net_if_addrs = psutil.net_if_addrs()
    net_if_stats = psutil.net_if_stats()
    
    for iface_name, addrs in net_if_addrs.items():
        stats = net_if_stats.get(iface_name)
        interfaces[iface_name] = {
            'is_up': stats.isup if stats else False,
            'speed': stats.speed if stats else 0,
            'addresses': [{'address': addr.address, 'family': str(addr.family)} 
                         for addr in addrs]
        }
    
    return {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv,
        'errin': net_io.errin,
        'errout': net_io.errout,
        'dropin': net_io.dropin,
        'dropout': net_io.dropout,
        'interfaces': interfaces
    }


def get_system_info():
    """시스템 기본 정보"""
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = time.time() - psutil.boot_time()
    
    return {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'hostname': platform.node(),
        'boot_time': boot_time.strftime('%Y-%m-%d %H:%M:%S'),
        'uptime_seconds': uptime,
        'process_count': len(psutil.pids())
    }


def get_process_info(limit=10):
    """상위 프로세스 목록 (CPU 사용량 기준)"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            pinfo = proc.info
            processes.append({
                'pid': pinfo['pid'],
                'name': pinfo['name'],
                'cpu_percent': pinfo['cpu_percent'] or 0,
                'memory_percent': pinfo['memory_percent'] or 0,
                'status': pinfo['status']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # CPU 사용량 기준 정렬
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return processes[:limit]


def format_bytes(bytes_val):
    """바이트를 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"
