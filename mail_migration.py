import imaplib, time, email, datetime, os, sys, re, threading
import schedule 
from email.header import decode_header

# --- 설정값 ---
NAVER_USER = "rakbinc"             
NAVER_PW = "EFDWLND7GXEP"   
GMAIL_USER = "franciscui@gmail.com" 
GMAIL_PW = "ovva qoqm pgeu vlhm"     

# BIN 요청: 하루 최대 400건 제한
BATCH_LIMIT = 400  
NEW_EMAIL_BATCH_LIMIT = 50 # 오늘 것은 넉넉히 실시간 전송
DELAY_BETWEEN_EMAILS = 2 

def load_processed_uids():
    if os.path.exists("processed_uids.txt"):
        with open("processed_uids.txt", "r") as f: return set(f.read().splitlines())
    return set()

def save_processed_uid(uid):
    with open("processed_uids.txt", "a") as f: f.write(f"{uid}\n")

def process_emails(email_ids, naver_imap, gmail_imap, processed_uids, limit):
    """메일을 원본 시간 그대로 삽입(APPEND) 합니다."""
    emails_to_forward = []
    # 중복 체크 먼저 수행
    for n_id in email_ids:
        try:
            _, uid_data = naver_imap.fetch(n_id, '(UID)')
            uid_str = uid_data[0].decode('utf-8').split('UID ')[1].replace(')', '').strip()
            if processed_uids is not None and uid_str in processed_uids:
                continue
            emails_to_forward.append((n_id, uid_str))
            if len(emails_to_forward) >= limit:
                break
        except: continue
    
    if not emails_to_forward:
        return 0, "처리할 메일이 없습니다."

    print(f"-> 전송 예정: {len(emails_to_forward)}건 (최신순 역방향 백업 시작)")
    
    success_count = 0
    for i, (n_id, uid_str) in enumerate(emails_to_forward, 1):
        try:
            _, data = naver_imap.fetch(n_id, '(RFC822 INTERNALDATE)')
            raw_email = data[0][1]
            attr_str = data[0][0].decode('utf-8', errors='ignore') 
            
            date_match = re.search(r'INTERNALDATE "([^"]+)"', attr_str)
            date_part = date_match.group(1) if date_match else imaplib.Time2Internaldate(time.time())

            # 날짜 강제 지정하여 지메일로 이관
            gmail_imap.append('INBOX', '\\Seen', f'"{date_part}"', raw_email)
            
            if processed_uids is not None:
                save_processed_uid(uid_str)
                
            success_count += 1
            msg_temp = email.message_from_bytes(raw_email)
            subject = decode_header(msg_temp.get('Subject') or "")[0][0]
            if isinstance(subject, bytes): subject = subject.decode('utf-8', 'ignore')
            
            # 윈도우 인코딩 오류 방지 처리하며 로그 출력
            log_msg = f"[{i}/{len(emails_to_forward)}] 전송완료: {str(subject)[:20]}... [{date_part}]"
            print(log_msg.encode('utf-8', 'replace').decode('utf-8'))
            
            time.sleep(DELAY_BETWEEN_EMAILS)
            
        except Exception as ex:
            print(f"[전송 오류]: {ex}")
            # 루프를 멈추지 않고(continue) 계속 진행 (시간 소중함!)
            continue
            
    return success_count, f"총 {success_count}건을 성공적으로 이관했습니다."

def migrate_history_emails():
    processed_uids = load_processed_uids()
    # 1년치를 검색하되, 뒤집어서(Reverse) '오늘로부터 가장 가까운' 것부터 400개
    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [히스토리] 최근 과거부터 거꾸로 백업")
    
    try:
        naver = imaplib.IMAP4_SSL("imap.naver.com")
        naver.login(NAVER_USER, NAVER_PW)
        naver.select("INBOX")
        
        gmail = imaplib.IMAP4_SSL("imap.gmail.com")
        gmail.login(GMAIL_USER, GMAIL_PW)
        
        # 365일치 리스트 확보
        one_year_ago = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%d-%b-%Y")
        status, data = naver.search(None, f'(SINCE "{one_year_ago}")')
        all_ids = data[0].split()
        
        # [중요] 최신순으로 뒤집어서 상위 400개를 처리함
        all_ids.reverse() 
        
        success_count, message = process_emails(all_ids, naver, gmail, processed_uids, BATCH_LIMIT)
        print(f"[히스토리 결과] {message}")
        
        naver.logout()
        gmail.logout()
    except Exception as e: 
        print(f"[히스토리 오류]: {e}")

def migrate_new_emails():
    processed_uids = load_processed_uids()
    # 실시간 범위는 항상 '어제와 오늘' (24시간+ 보장)
    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d-%b-%Y")
    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [실시간] 신규 메일 상시 감시 중 (최근 24h+)")
    try:
        naver = imaplib.IMAP4_SSL("imap.naver.com")
        naver.login(NAVER_USER, NAVER_PW)
        naver.select("INBOX")
        gmail = imaplib.IMAP4_SSL("imap.gmail.com")
        gmail.login(GMAIL_USER, GMAIL_PW)

        status, data = naver.search(None, f'(SINCE "{yesterday_str}")')
        all_ids = data[0].split()
        all_ids.reverse() # 최신 메일 최우선 전송
        
        success_count, message = process_emails(all_ids, naver, gmail, processed_uids, NEW_EMAIL_BATCH_LIMIT)
        if success_count > 0:
            print(f"[실시간 결과] {message}")
        
        naver.logout()
        gmail.logout()
    except Exception as e:
        print(f"[실시간 오류]: {e}")

def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

if __name__ == "__main__":
    print("===== BIN 날짜 보완 시스템 3.0 (최신지향형) 가동 =====")
    print("실시간 모니터링 및 가장 가까운 과거(어제 등) 메일 우선 복구 모드입니다.")
    
    schedule.every().day.at("01:00").do(run_threaded, migrate_history_emails)
    schedule.every(5).minutes.do(run_threaded, migrate_new_emails)
    
    # 즉시 시작 (실시간 감시부터 먼저!)
    run_threaded(migrate_new_emails)
    time.sleep(2) # 약간의 간격을 둡니다.
    run_threaded(migrate_history_emails)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
