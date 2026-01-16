"""
온도 센서 정보 수집기
Windows WMI를 사용한 CPU 온도 모니터링
"""

import platform

# Windows에서만 WMI 사용
if platform.system() == 'Windows':
    try:
        import wmi
        WMI_AVAILABLE = True
    except ImportError:
        WMI_AVAILABLE = False
else:
    WMI_AVAILABLE = False


def get_cpu_temperature():
    """CPU 온도 수집 (Windows)"""
    if not WMI_AVAILABLE:
        return {'available': False, 'temperature': None, 'error': 'WMI not available'}
    
    try:
        w = wmi.WMI(namespace="root\\wmi")
        temperature_info = w.MSAcpi_ThermalZoneTemperature()
        
        if temperature_info:
            # 온도는 0.1K 단위로 제공됨, 섭씨로 변환
            temp_kelvin = temperature_info[0].CurrentTemperature
            temp_celsius = (temp_kelvin / 10.0) - 273.15
            return {
                'available': True,
                'temperature': round(temp_celsius, 1),
                'error': None
            }
        else:
            return {'available': False, 'temperature': None, 'error': 'No temperature data'}
    
    except Exception as e:
        # 대체 방법: OpenHardwareMonitor WMI
        try:
            return get_temperature_ohm()
        except:
            return {'available': False, 'temperature': None, 'error': str(e)}


def get_temperature_ohm():
    """OpenHardwareMonitor WMI로 온도 수집"""
    if not WMI_AVAILABLE:
        return {'available': False, 'temperature': None, 'error': 'WMI not available'}
    
    try:
        w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        sensors = w.Sensor()
        
        temperatures = []
        for sensor in sensors:
            if sensor.SensorType == 'Temperature':
                temperatures.append({
                    'name': sensor.Name,
                    'value': sensor.Value,
                    'hardware': sensor.Parent
                })
        
        if temperatures:
            # CPU 온도 찾기
            cpu_temps = [t for t in temperatures if 'CPU' in t['name'].upper()]
            if cpu_temps:
                return {
                    'available': True,
                    'temperature': round(cpu_temps[0]['value'], 1),
                    'all_temperatures': temperatures,
                    'error': None
                }
        
        return {'available': False, 'temperature': None, 'error': 'No CPU temperature found'}
    
    except Exception as e:
        return {'available': False, 'temperature': None, 'error': str(e)}


def get_all_temperatures():
    """모든 온도 센서 정보"""
    result = {
        'cpu': get_cpu_temperature(),
        'sensors': []
    }
    
    # psutil 센서 시도 (Linux에서 주로 작동)
    try:
        import psutil
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            for entry in entries:
                result['sensors'].append({
                    'name': f"{name}: {entry.label or 'N/A'}",
                    'current': entry.current,
                    'high': entry.high,
                    'critical': entry.critical
                })
    except:
        pass
    
    return result
