import time
import os
import subprocess
import urllib.request
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# Configuration
API_URL = 'http://localhost:8001/v2/memories/'
HEADERS = {'X-API-Key': 'test-key', 'X-Tenant-Id': '00000000-0000-0000-0000-000000000000'}
WORK_DIR = '/app/agent_hive/work_dir/components/'
COMPOSE_DIR = '/app/agent_hive/'

# SMTP Configuration (Verified Credentials)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "vproject.111@gmail.com" 
SMTP_PASS = "mwzmjsunp"
REPORT_EMAIL = "vproject.111@gmail.com"

def log_to_rae(msg, tags=[]):
    payload = {"content": f"[SUPERVISOR] {msg}", "layer": "reflective", "tags": ["supervisor_log"] + tags}
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json', **HEADERS}, method='POST')
        urllib.request.urlopen(req, timeout=10)
    except: pass

def send_email(subject, body):
    if not SMTP_USER or not SMTP_PASS:
        print(f"Skipping email (no credentials): {subject}")
        return
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = REPORT_EMAIL
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        log_to_rae(f"Email sent: {subject}", ["email_sent"])
    except Exception as e:
        log_to_rae(f"Email failed: {e}", ["error"])

def get_stats():
    # Count .tsx files
    try:
        tsx_count = len([f for f in os.listdir(WORK_DIR) if f.endswith('.tsx')])
    except: tsx_count = 0
    
    # Count Graph Edges via local psql check (inside container)
    try:
        res = subprocess.check_output("psql -U rae -d rae -t -c 'SELECT count(*) FROM memory_neighbors;'", shell=True)
        graph_count = int(res.decode().strip())
    except: graph_count = 0
    
    # Count Semantic Memories
    try:
        res = subprocess.check_output("psql -U rae -d rae -t -c "SELECT count(*) FROM memories WHERE layer = 'semantic';"", shell=True)
        mem_count = int(res.decode().strip())
    except: mem_count = 0
    
    return tsx_count, graph_count, mem_count

last_tsx, last_graph, last_mem = get_stats()
last_report_time = time.time()

print("🕵️ Supervisor LTS v2.2 active. Monitoring Oracle Graph & Dreamsoft Factory...")
log_to_rae("Supervisor LTS v2.2 started. Reporting configured to vproject.111@gmail.com")
send_email("RAE Factory: Supervisor Online", "RAE Factory Supervisor has been restored and is monitoring progress.")

while True:
    time.sleep(300) # Check every 5 minutes
    current_tsx, current_graph, current_mem = get_stats()
    now = time.time()
    
    # 1. 2-Hour Periodic Report
    if now - last_report_time >= 7200:
        report = f"Periodic Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}
"
        report += f"- Generated Components: {current_tsx}
"
        report += f"- Knowledge Graph Edges: {current_graph}
"
        report += f"- Semantic Memories: {current_mem}
"
        report += f"- System State: Operational"
        
        log_to_rae(report, ["periodic_report"])
        send_email("RAE Factory: 2h Status Update", report)
        last_report_time = now

    # 2. Stall Detection
    if current_tsx == last_tsx and current_graph == last_graph and current_mem == last_mem:
        # Check if ingestion is still active
        msg = "Potential STALL detected. No progress in 5 mins."
        log_to_rae(msg, ["warning", "stall_check"])
    
    # 3. Progress Update
    if current_tsx > last_tsx or current_graph > last_graph or current_mem > last_mem:
        log_to_rae(f"Progress: TSX={current_tsx}, Graph={current_graph}, Mem={current_mem}", ["progress"])
        last_tsx, last_graph, last_mem = current_tsx, current_graph, current_mem
