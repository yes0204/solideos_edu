# 시스템 리소스 모니터링 시스템

실시간 시스템 리소스 모니터링 웹 대시보드 (Python/Flask)

## 기능

- **CPU**: 사용률, 코어별 사용률, 주파수, 온도
- **메모리**: RAM/Swap 사용량
- **디스크**: 파티션 용량, Read/Write I/O
- **네트워크**: 송수신 속도, 총 트래픽
- **GPU**: NVIDIA GPU 사용률, VRAM, 온도
- **프로세스**: 상위 프로세스 목록

## 스크린샷

실시간 대시보드 UI (다크 모드, glassmorphism 디자인)

## 설치 및 실행

```bash
pip install -r requirements.txt
python app.py
```

브라우저에서 http://localhost:5000 접속

## PDF 보고서 생성

5분간 데이터 수집 후 PDF 보고서 생성:

```bash
python generate_report.py
```

생성된 보고서는 `reports/` 폴더에 저장됩니다.

## 기술 스택

- **Backend**: Python Flask
- **모니터링**: psutil, GPUtil, WMI
- **Frontend**: HTML/CSS/JavaScript, Chart.js
- **PDF**: matplotlib, ReportLab

## 프로젝트 구조

```
system-monitor/
├── app.py                    # Flask 웹 서버
├── requirements.txt          # Python 의존성
├── generate_report.py        # 독립 PDF 생성
├── collectors/               # 데이터 수집기
│   ├── system_info.py
│   ├── gpu_info.py
│   └── temperature.py
├── report/
│   └── pdf_generator.py
└── static/
    ├── index.html
    ├── css/style.css
    └── js/dashboard.js
```

## 라이선스

MIT License
