"""
PDF 보고서 직접 생성 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from collections import defaultdict
import time

from collectors.system_info import (
    get_cpu_info, get_memory_info, get_disk_info, 
    get_network_info, get_system_info
)
from collectors.gpu_info import get_gpu_summary
from collectors.temperature import get_cpu_temperature
from report.pdf_generator import generate_pdf_report

def collect_sample_data(duration_seconds=60, interval=1):
    """샘플 데이터 수집"""
    print(f"데이터 수집 시작 ({duration_seconds}초)...")
    
    history = defaultdict(list)
    last_network = None
    last_disk_io = None
    
    # 시스템 정보
    history['system_info'] = get_system_info()
    
    start_time = time.time()
    while (time.time() - start_time) < duration_seconds:
        now = datetime.now()
        elapsed = int(time.time() - start_time)
        print(f"  수집 중... {elapsed}/{duration_seconds}초", end='\r')
        
        # CPU
        cpu = get_cpu_info()
        history['cpu'].append({'time': now, 'value': cpu['usage_percent']})
        
        # 메모리
        mem = get_memory_info()
        history['memory'].append({'time': now, 'value': mem['percent']})
        
        # 네트워크
        net = get_network_info()
        if last_network:
            sent_per_sec = (net['bytes_sent'] - last_network['bytes_sent']) / 1024 / 1024
            recv_per_sec = (net['bytes_recv'] - last_network['bytes_recv']) / 1024 / 1024
            history['network_sent'].append({'time': now, 'value': max(0, sent_per_sec)})
            history['network_recv'].append({'time': now, 'value': max(0, recv_per_sec)})
        last_network = net
        
        # 디스크 I/O
        disk = get_disk_info()
        if last_disk_io:
            read_per_sec = (disk['io']['read_bytes'] - last_disk_io['read_bytes']) / 1024 / 1024
            write_per_sec = (disk['io']['write_bytes'] - last_disk_io['write_bytes']) / 1024 / 1024
            history['disk_read'].append({'time': now, 'value': max(0, read_per_sec)})
            history['disk_write'].append({'time': now, 'value': max(0, write_per_sec)})
        last_disk_io = disk['io']
        
        # 디스크 파티션
        history['disk_partitions'] = disk['partitions']
        
        # GPU
        gpu = get_gpu_summary()
        if gpu:
            history['gpu'].append({'time': now, 'value': gpu['usage_percent']})
        
        time.sleep(interval)
    
    print(f"\n데이터 수집 완료! {len(history['cpu'])}개 데이터 포인트")
    return dict(history)


def main():
    print("=" * 60)
    print("  시스템 리소스 모니터링 - PDF 보고서 생성")
    print("=" * 60)
    
    # 5분(300초) 데이터 수집
    history = collect_sample_data(duration_seconds=300, interval=1)
    
    # PDF 생성
    output_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    print(f"\nPDF 보고서 생성 중...")
    try:
        generate_pdf_report(history, output_path)
        print(f"✅ PDF 보고서 생성 완료: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    main()
