"""
시스템 리소스 모니터링 서버
Flask 웹 서버 + REST API
"""

from flask import Flask, jsonify, render_template, send_file, send_from_directory
from flask_cors import CORS
from datetime import datetime
from collections import defaultdict
import threading
import time
import os

# 컬렉터 임포트
from collectors.system_info import (
    get_cpu_info, get_memory_info, get_disk_info, 
    get_network_info, get_system_info, get_process_info, format_bytes
)
from collectors.gpu_info import get_gpu_info, get_gpu_summary
from collectors.temperature import get_cpu_temperature, get_all_temperatures
from report.pdf_generator import generate_pdf_report


app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# 데이터 히스토리 저장소
history = defaultdict(list)
last_network = None
last_disk_io = None
monitoring_active = False
monitoring_start_time = None

# 시스템 정보 캐시
system_info_cache = None

# 5분 = 300초
MONITORING_DURATION = 300


def collect_data():
    """데이터 수집"""
    global last_network, last_disk_io, system_info_cache
    
    now = datetime.now()
    
    # CPU
    cpu = get_cpu_info()
    history['cpu'].append({'time': now, 'value': cpu['usage_percent']})
    
    # 메모리
    mem = get_memory_info()
    history['memory'].append({'time': now, 'value': mem['percent']})
    
    # 네트워크 (초당 전송량 계산)
    net = get_network_info()
    if last_network:
        sent_per_sec = (net['bytes_sent'] - last_network['bytes_sent']) / 1024 / 1024  # MB/s
        recv_per_sec = (net['bytes_recv'] - last_network['bytes_recv']) / 1024 / 1024  # MB/s
        history['network_sent'].append({'time': now, 'value': max(0, sent_per_sec)})
        history['network_recv'].append({'time': now, 'value': max(0, recv_per_sec)})
    last_network = net
    
    # 디스크 I/O (초당 전송량 계산)
    disk = get_disk_info()
    if last_disk_io:
        read_per_sec = (disk['io']['read_bytes'] - last_disk_io['read_bytes']) / 1024 / 1024
        write_per_sec = (disk['io']['write_bytes'] - last_disk_io['write_bytes']) / 1024 / 1024
        history['disk_read'].append({'time': now, 'value': max(0, read_per_sec)})
        history['disk_write'].append({'time': now, 'value': max(0, write_per_sec)})
    last_disk_io = disk['io']
    
    # 디스크 파티션 정보 (가장 최근 것만)
    history['disk_partitions'] = disk['partitions']
    
    # GPU
    gpu = get_gpu_summary()
    if gpu:
        history['gpu'].append({'time': now, 'value': gpu['usage_percent']})
        history['gpu_temp'].append({'time': now, 'value': gpu['temperature'] or 0})
        history['gpu_memory'].append({'time': now, 'value': gpu['memory_percent']})
    
    # CPU 온도
    temp = get_cpu_temperature()
    if temp['available']:
        history['cpu_temp'].append({'time': now, 'value': temp['temperature']})
    
    # 시스템 정보 캐시
    if not system_info_cache:
        system_info_cache = get_system_info()
    history['system_info'] = system_info_cache


def monitoring_thread():
    """백그라운드 모니터링 스레드"""
    global monitoring_active
    
    while monitoring_active:
        collect_data()
        time.sleep(1)


def start_monitoring():
    """모니터링 시작"""
    global monitoring_active, monitoring_start_time, history
    global last_network, last_disk_io, system_info_cache
    
    # 이전 데이터 초기화
    history = defaultdict(list)
    last_network = None
    last_disk_io = None
    system_info_cache = None
    
    monitoring_active = True
    monitoring_start_time = datetime.now()
    
    thread = threading.Thread(target=monitoring_thread, daemon=True)
    thread.start()


def stop_monitoring():
    """모니터링 중지"""
    global monitoring_active
    monitoring_active = False


@app.route('/')
def index():
    """메인 대시보드"""
    return send_from_directory('static', 'index.html')


@app.route('/api/status')
def get_status():
    """모니터링 상태"""
    elapsed = 0
    if monitoring_start_time:
        elapsed = (datetime.now() - monitoring_start_time).seconds
    
    return jsonify({
        'active': monitoring_active,
        'elapsed_seconds': elapsed,
        'target_seconds': MONITORING_DURATION,
        'data_points': len(history.get('cpu', []))
    })


@app.route('/api/start')
def api_start():
    """모니터링 시작 API"""
    start_monitoring()
    return jsonify({'status': 'started'})


@app.route('/api/stop')
def api_stop():
    """모니터링 중지 API"""
    stop_monitoring()
    return jsonify({'status': 'stopped'})


@app.route('/api/data')
def get_data():
    """실시간 데이터 API"""
    # 최신 데이터 수집
    cpu = get_cpu_info()
    mem = get_memory_info()
    disk = get_disk_info()
    net = get_network_info()
    gpu = get_gpu_info()
    temp = get_all_temperatures()
    procs = get_process_info(10)
    sys_info = get_system_info()
    
    # 네트워크 속도 계산
    global last_network
    net_sent_speed = 0
    net_recv_speed = 0
    if last_network:
        net_sent_speed = (net['bytes_sent'] - last_network['bytes_sent']) / 1024 / 1024
        net_recv_speed = (net['bytes_recv'] - last_network['bytes_recv']) / 1024 / 1024
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'cpu': cpu,
        'memory': mem,
        'disk': disk,
        'network': {
            **net,
            'speed_sent': max(0, net_sent_speed),
            'speed_recv': max(0, net_recv_speed)
        },
        'gpu': gpu,
        'temperature': temp,
        'processes': procs,
        'system': sys_info
    })


@app.route('/api/history')
def get_history():
    """히스토리 데이터 API (차트용)"""
    def serialize(data_list):
        return [{'time': d['time'].isoformat(), 'value': d['value']} for d in data_list[-60:]]
    
    return jsonify({
        'cpu': serialize(history.get('cpu', [])),
        'memory': serialize(history.get('memory', [])),
        'network_sent': serialize(history.get('network_sent', [])),
        'network_recv': serialize(history.get('network_recv', [])),
        'disk_read': serialize(history.get('disk_read', [])),
        'disk_write': serialize(history.get('disk_write', [])),
        'gpu': serialize(history.get('gpu', [])),
        'gpu_temp': serialize(history.get('gpu_temp', [])),
        'cpu_temp': serialize(history.get('cpu_temp', []))
    })


@app.route('/api/report')
def generate_report():
    """PDF 보고서 생성 API"""
    global history
    
    if not history.get('cpu'):
        return jsonify({'error': 'No data collected. Start monitoring first.'}), 400
    
    # 보고서 저장 경로
    output_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    try:
        generate_pdf_report(dict(history), output_path)
        return send_file(output_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  시스템 리소스 모니터링 서버")
    print("  http://localhost:5000 에서 대시보드 확인")
    print("="*60 + "\n")
    
    # 서버 시작 시 자동으로 모니터링 시작
    start_monitoring()
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
