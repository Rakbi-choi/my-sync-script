# [검증용: Python 기반 동기화 감시 스크립트 - 경로 설정 필요]
import os
import time
import subprocess

# BIN님의 실제 경로로 수정이 필요한 부분
SYNC_PATH = r"C:\Cloud_Sync" 

def check_services():
    # 구글 드라이브와 네이버 마이박스 프로세스가 실행 중인지 체크
    services = ["GoogleDriveFS.exe", "NaverCloud.exe"]
    for service in services:
        output = subprocess.getoutput(f'tasklist /FI "IMAGENAME eq {service}"')
        if service not in output:
            print(f"경고: {service}가 실행 중이지 않습니다. 재시작이 필요합니다.")

def monitor_sync():
    print(f"[{time.ctime()}] 모니터링을 시작합니다: {SYNC_PATH}")
    while True:
        check_services()
        # 여기에 추가적인 파일 정합성 체크 로직 삽입 가능
        time.sleep(300) # 5분 간격 체크

# 실행 허락이 떨어지면 BIN님의 환경에 맞춰 최종 코드를 확정하겠습니다.
