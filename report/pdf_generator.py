"""
PDF 보고서 생성기
matplotlib 차트 + ReportLab PDF
"""

import io
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict


# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


def create_chart(data, title, ylabel, filename):
    """시계열 차트 생성"""
    fig, ax = plt.subplots(figsize=(10, 4))
    
    times = [d['time'] for d in data]
    values = [d['value'] for d in data]
    
    ax.plot(times, values, 'b-', linewidth=1.5, color='#3498db')
    ax.fill_between(times, values, alpha=0.3, color='#3498db')
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylabel(ylabel)
    ax.set_xlabel('시간')
    
    # X축 포맷
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, max(max(values) * 1.1, 100) if values else 100)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filename


def create_multi_chart(datasets, title, ylabel, filename, legends=None):
    """여러 데이터셋 차트"""
    fig, ax = plt.subplots(figsize=(10, 4))
    
    colors_list = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
    
    for i, data in enumerate(datasets):
        times = [d['time'] for d in data]
        values = [d['value'] for d in data]
        color = colors_list[i % len(colors_list)]
        label = legends[i] if legends and i < len(legends) else f'Data {i+1}'
        ax.plot(times, values, linewidth=1.5, color=color, label=label)
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylabel(ylabel)
    ax.set_xlabel('시간')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filename


def generate_pdf_report(history_data, output_path):
    """PDF 보고서 생성"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    
    # 커스텀 스타일
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#34495e')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8
    )
    
    elements = []
    
    # 제목
    elements.append(Paragraph("시스템 리소스 모니터링 보고서", title_style))
    elements.append(Paragraph(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                             ParagraphStyle('Center', alignment=TA_CENTER, fontSize=12)))
    elements.append(Spacer(1, 20))
    
    # 모니터링 기간
    if history_data['cpu']:
        start_time = history_data['cpu'][0]['time'].strftime('%H:%M:%S')
        end_time = history_data['cpu'][-1]['time'].strftime('%H:%M:%S')
        duration = len(history_data['cpu'])
        elements.append(Paragraph(f"모니터링 기간: {start_time} ~ {end_time} ({duration}초)", normal_style))
    
    elements.append(Spacer(1, 20))
    
    # 시스템 정보 테이블
    if history_data.get('system_info'):
        elements.append(Paragraph("시스템 정보", heading_style))
        sys_info = history_data['system_info']
        sys_data = [
            ['항목', '값'],
            ['호스트명', sys_info.get('hostname', 'N/A')],
            ['OS', f"{sys_info.get('platform', 'N/A')} {sys_info.get('platform_release', '')}"],
            ['프로세서', sys_info.get('processor', 'N/A')],
            ['부팅 시간', sys_info.get('boot_time', 'N/A')],
        ]
        
        sys_table = Table(sys_data, colWidths=[4*cm, 12*cm])
        sys_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ]))
        elements.append(sys_table)
        elements.append(Spacer(1, 20))
    
    # 통계 요약
    elements.append(Paragraph("리소스 사용량 통계", heading_style))
    
    stats_data = [['리소스', '평균', '최소', '최대']]
    
    for key, label in [('cpu', 'CPU (%)'), ('memory', '메모리 (%)'), 
                       ('network_sent', '네트워크 송신 (MB/s)'), 
                       ('network_recv', '네트워크 수신 (MB/s)')]:
        if history_data.get(key) and len(history_data[key]) > 0:
            values = [d['value'] for d in history_data[key]]
            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            stats_data.append([label, f"{avg:.2f}", f"{min_val:.2f}", f"{max_val:.2f}"])
    
    if len(stats_data) > 1:
        stats_table = Table(stats_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ]))
        elements.append(stats_table)
    
    elements.append(PageBreak())
    
    # 차트 섹션
    temp_dir = os.path.dirname(output_path)
    
    # CPU 사용량 차트
    if history_data.get('cpu') and len(history_data['cpu']) > 1:
        elements.append(Paragraph("CPU 사용량 추이", heading_style))
        cpu_chart = os.path.join(temp_dir, 'cpu_chart.png')
        create_chart(history_data['cpu'], 'CPU 사용량 (%)', '사용률 (%)', cpu_chart)
        elements.append(Image(cpu_chart, width=16*cm, height=6*cm))
        elements.append(Spacer(1, 20))
    
    # 메모리 사용량 차트
    if history_data.get('memory') and len(history_data['memory']) > 1:
        elements.append(Paragraph("메모리 사용량 추이", heading_style))
        mem_chart = os.path.join(temp_dir, 'memory_chart.png')
        create_chart(history_data['memory'], '메모리 사용량 (%)', '사용률 (%)', mem_chart)
        elements.append(Image(mem_chart, width=16*cm, height=6*cm))
        elements.append(Spacer(1, 20))
    
    # 네트워크 트래픽 차트
    if (history_data.get('network_sent') and history_data.get('network_recv') and 
        len(history_data['network_sent']) > 1):
        elements.append(Paragraph("네트워크 트래픽 추이", heading_style))
        net_chart = os.path.join(temp_dir, 'network_chart.png')
        create_multi_chart(
            [history_data['network_sent'], history_data['network_recv']],
            '네트워크 트래픽 (MB/s)',
            '속도 (MB/s)',
            net_chart,
            legends=['송신', '수신']
        )
        elements.append(Image(net_chart, width=16*cm, height=6*cm))
        elements.append(Spacer(1, 20))
    
    # 디스크 I/O 차트
    if (history_data.get('disk_read') and history_data.get('disk_write') and 
        len(history_data['disk_read']) > 1):
        elements.append(PageBreak())
        elements.append(Paragraph("디스크 I/O 추이", heading_style))
        disk_chart = os.path.join(temp_dir, 'disk_chart.png')
        create_multi_chart(
            [history_data['disk_read'], history_data['disk_write']],
            '디스크 I/O (MB/s)',
            '속도 (MB/s)',
            disk_chart,
            legends=['읽기', '쓰기']
        )
        elements.append(Image(disk_chart, width=16*cm, height=6*cm))
        elements.append(Spacer(1, 20))
    
    # GPU 정보
    if history_data.get('gpu') and len(history_data['gpu']) > 1:
        elements.append(Paragraph("GPU 사용량 추이", heading_style))
        gpu_chart = os.path.join(temp_dir, 'gpu_chart.png')
        create_chart(history_data['gpu'], 'GPU 사용량 (%)', '사용률 (%)', gpu_chart)
        elements.append(Image(gpu_chart, width=16*cm, height=6*cm))
    
    # 디스크 사용량 테이블
    if history_data.get('disk_partitions'):
        elements.append(PageBreak())
        elements.append(Paragraph("디스크 파티션 상태", heading_style))
        
        disk_data = [['드라이브', '파일시스템', '전체', '사용', '사용률']]
        for part in history_data['disk_partitions']:
            disk_data.append([
                part['mountpoint'],
                part['fstype'],
                f"{part['total'] / (1024**3):.1f} GB",
                f"{part['used'] / (1024**3):.1f} GB",
                f"{part['percent']:.1f}%"
            ])
        
        disk_table = Table(disk_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
        disk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ]))
        elements.append(disk_table)
    
    # PDF 생성
    doc.build(elements)
    
    # 임시 차트 파일 삭제
    for f in ['cpu_chart.png', 'memory_chart.png', 'network_chart.png', 
              'disk_chart.png', 'gpu_chart.png']:
        path = os.path.join(temp_dir, f)
        if os.path.exists(path):
            os.remove(path)
    
    return output_path
