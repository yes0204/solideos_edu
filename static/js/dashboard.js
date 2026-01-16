/**
 * 시스템 리소스 모니터 - 대시보드 JavaScript
 */

// Chart.js 기본 설정
Chart.defaults.color = '#a0a0b0';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

// 차트 인스턴스
let cpuChart, memoryChart, networkChart, diskChart;

// 차트 데이터 히스토리
const maxDataPoints = 60;
const chartData = {
    cpu: [],
    memory: [],
    networkSent: [],
    networkRecv: [],
    diskRead: [],
    diskWrite: [],
    labels: []
};

// 차트 초기화
function initCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        scales: {
            x: {
                display: true,
                grid: { display: false },
                ticks: { maxTicksLimit: 10 }
            },
            y: {
                beginAtZero: true,
                max: 100,
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
            }
        },
        plugins: {
            legend: { display: false }
        },
        elements: {
            point: { radius: 0 },
            line: { tension: 0.4 }
        }
    };

    // CPU 차트
    cpuChart = new Chart(document.getElementById('cpuChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CPU %',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                borderWidth: 2
            }]
        },
        options: { ...chartOptions }
    });

    // 메모리 차트
    memoryChart = new Chart(document.getElementById('memoryChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Memory %',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                borderWidth: 2
            }]
        },
        options: { ...chartOptions }
    });

    // 네트워크 차트
    const networkOptions = { ...chartOptions };
    networkOptions.scales.y.max = undefined;
    
    networkChart = new Chart(document.getElementById('networkChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '송신 MB/s',
                    data: [],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    fill: true,
                    borderWidth: 2
                },
                {
                    label: '수신 MB/s',
                    data: [],
                    borderColor: '#ec4899',
                    backgroundColor: 'rgba(236, 72, 153, 0.1)',
                    fill: true,
                    borderWidth: 2
                }
            ]
        },
        options: {
            ...networkOptions,
            plugins: {
                legend: { display: true, position: 'top' }
            }
        }
    });

    // 디스크 I/O 차트
    diskChart = new Chart(document.getElementById('diskChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: '읽기 MB/s',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    borderWidth: 2
                },
                {
                    label: '쓰기 MB/s',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    borderWidth: 2
                }
            ]
        },
        options: {
            ...networkOptions,
            plugins: {
                legend: { display: true, position: 'top' }
            }
        }
    });
}

// 바이트 포맷
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 시간 포맷
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// 데이터 업데이트
async function updateData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        const now = new Date();
        const timeLabel = now.toLocaleTimeString('ko-KR', { hour12: false });
        
        // CPU 업데이트
        document.getElementById('cpuValue').textContent = data.cpu.usage_percent.toFixed(1);
        document.getElementById('cpuFreq').textContent = `${Math.round(data.cpu.frequency_current)} MHz`;
        document.getElementById('cpuCores').textContent = `${data.cpu.cores_physical}C / ${data.cpu.cores_logical}T`;
        document.getElementById('cpuProgress').style.width = `${data.cpu.usage_percent}%`;
        
        // CPU 온도
        if (data.temperature && data.temperature.cpu && data.temperature.cpu.available) {
            document.getElementById('cpuTemp').textContent = `${data.temperature.cpu.temperature}°C`;
        }
        
        // 메모리 업데이트
        document.getElementById('memValue').textContent = data.memory.percent.toFixed(1);
        document.getElementById('memUsed').textContent = formatBytes(data.memory.used);
        document.getElementById('memTotal').textContent = formatBytes(data.memory.total);
        document.getElementById('memAvailable').textContent = formatBytes(data.memory.available);
        document.getElementById('memProgress').style.width = `${data.memory.percent}%`;
        
        // GPU 업데이트
        if (data.gpu.available && data.gpu.gpus.length > 0) {
            const gpu = data.gpu.gpus[0];
            document.getElementById('gpuValue').textContent = gpu.load.toFixed(1);
            document.getElementById('gpuUnit').textContent = '%';
            document.getElementById('gpuName').textContent = gpu.name.substring(0, 20);
            document.getElementById('gpuMemory').textContent = `${Math.round(gpu.memory_used)} / ${Math.round(gpu.memory_total)} MB`;
            document.getElementById('gpuTemp').textContent = gpu.temperature ? `${gpu.temperature}°C` : 'N/A';
            document.getElementById('gpuProgress').style.width = `${gpu.load}%`;
        }
        
        // 네트워크 업데이트
        document.getElementById('netSent').textContent = data.network.speed_sent.toFixed(2);
        document.getElementById('netRecv').textContent = data.network.speed_recv.toFixed(2);
        document.getElementById('netTotalSent').textContent = formatBytes(data.network.bytes_sent);
        document.getElementById('netTotalRecv').textContent = formatBytes(data.network.bytes_recv);
        
        // 차트 데이터 추가
        chartData.labels.push(timeLabel);
        chartData.cpu.push(data.cpu.usage_percent);
        chartData.memory.push(data.memory.percent);
        chartData.networkSent.push(data.network.speed_sent);
        chartData.networkRecv.push(data.network.speed_recv);
        
        // 디스크 I/O (간단히 0으로 설정, 실제로는 이전 값과 비교 필요)
        chartData.diskRead.push(0);
        chartData.diskWrite.push(0);
        
        // 최대 데이터 포인트 유지
        if (chartData.labels.length > maxDataPoints) {
            chartData.labels.shift();
            chartData.cpu.shift();
            chartData.memory.shift();
            chartData.networkSent.shift();
            chartData.networkRecv.shift();
            chartData.diskRead.shift();
            chartData.diskWrite.shift();
        }
        
        // 차트 업데이트
        updateCharts();
        
        // 디스크 파티션
        updateDiskPartitions(data.disk.partitions);
        
        // 프로세스 테이블
        updateProcessTable(data.processes);
        
        // 시스템 정보
        updateSystemInfo(data.system);
        
        // 호스트명
        document.getElementById('hostname').textContent = data.system.hostname;
        
    } catch (error) {
        console.error('데이터 업데이트 오류:', error);
    }
}

// 차트 업데이트
function updateCharts() {
    cpuChart.data.labels = chartData.labels;
    cpuChart.data.datasets[0].data = chartData.cpu;
    cpuChart.update('none');
    
    memoryChart.data.labels = chartData.labels;
    memoryChart.data.datasets[0].data = chartData.memory;
    memoryChart.update('none');
    
    networkChart.data.labels = chartData.labels;
    networkChart.data.datasets[0].data = chartData.networkSent;
    networkChart.data.datasets[1].data = chartData.networkRecv;
    networkChart.update('none');
    
    diskChart.data.labels = chartData.labels;
    diskChart.data.datasets[0].data = chartData.diskRead;
    diskChart.data.datasets[1].data = chartData.diskWrite;
    diskChart.update('none');
}

// 디스크 파티션 업데이트
function updateDiskPartitions(partitions) {
    const container = document.getElementById('diskPartitions');
    container.innerHTML = partitions.map(p => `
        <div class="disk-item">
            <div class="disk-item-header">
                <span class="drive">${p.mountpoint}</span>
                <span>${formatBytes(p.used)} / ${formatBytes(p.total)}</span>
            </div>
            <div class="disk-progress">
                <div class="disk-progress-fill" style="width: ${p.percent}%"></div>
            </div>
        </div>
    `).join('');
}

// 프로세스 테이블 업데이트
function updateProcessTable(processes) {
    const tbody = document.getElementById('processTable');
    tbody.innerHTML = processes.map(p => `
        <tr>
            <td>${p.pid}</td>
            <td>${p.name.substring(0, 30)}</td>
            <td>${p.cpu_percent.toFixed(1)}%</td>
            <td>${p.memory_percent.toFixed(1)}%</td>
        </tr>
    `).join('');
}

// 시스템 정보 업데이트
function updateSystemInfo(system) {
    const container = document.getElementById('systemInfo');
    
    const uptime = formatUptime(system.uptime_seconds);
    
    container.innerHTML = `
        <div class="system-info-item">
            <div class="label">운영체제</div>
            <div class="value">${system.platform} ${system.platform_release}</div>
        </div>
        <div class="system-info-item">
            <div class="label">프로세서</div>
            <div class="value">${system.processor || 'N/A'}</div>
        </div>
        <div class="system-info-item">
            <div class="label">부팅 시간</div>
            <div class="value">${system.boot_time}</div>
        </div>
        <div class="system-info-item">
            <div class="label">가동 시간</div>
            <div class="value">${uptime}</div>
        </div>
        <div class="system-info-item">
            <div class="label">아키텍처</div>
            <div class="value">${system.architecture}</div>
        </div>
        <div class="system-info-item">
            <div class="label">프로세스 수</div>
            <div class="value">${system.process_count}</div>
        </div>
    `;
}

// 가동 시간 포맷
function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    
    let result = '';
    if (days > 0) result += `${days}일 `;
    if (hours > 0) result += `${hours}시간 `;
    result += `${mins}분`;
    
    return result;
}

// 모니터링 상태 업데이트
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('monitoringStatus');
        const elapsedText = document.getElementById('elapsedTime');
        
        if (status.active) {
            statusDot.classList.remove('inactive');
            statusText.textContent = '모니터링 중';
            elapsedText.textContent = formatTime(status.elapsed_seconds) + ' / ' + formatTime(status.target_seconds);
        } else {
            statusDot.classList.add('inactive');
            statusText.textContent = '대기 중';
        }
    } catch (error) {
        console.error('상태 업데이트 오류:', error);
    }
}

// PDF 보고서 생성
async function generateReport() {
    const btn = document.getElementById('btnReport');
    btn.disabled = true;
    btn.textContent = '⏳ 생성 중...';
    
    try {
        const response = await fetch('/api/report');
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `system_report_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            
            alert('PDF 보고서가 생성되었습니다!');
        } else {
            const error = await response.json();
            alert('오류: ' + error.error);
        }
    } catch (error) {
        alert('PDF 생성 중 오류가 발생했습니다.');
        console.error(error);
    } finally {
        btn.disabled = false;
        btn.textContent = '📄 PDF 보고서 생성';
    }
}

// 시간 표시 업데이트
function updateDateTime() {
    const now = new Date();
    document.getElementById('datetime').textContent = now.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    updateData();
    updateStatus();
    updateDateTime();
    
    // 1초마다 데이터 업데이트
    setInterval(updateData, 1000);
    setInterval(updateStatus, 1000);
    setInterval(updateDateTime, 1000);
});
