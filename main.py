import threading
import time
import requests
import re
import os
import logging
from flask import Flask, jsonify, request

# سیٹ اپ
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

CREDENTIALS = {
    "username": "Kami522",
    "password": "Kami526"
}

BASE_URL = "http://51.89.99.105/NumberPanel"
URL_NUMBERS_BASE = "http://51.89.99.105/NumberPanel/client/res/data_smsnumbers.php?frange=&fclient=&sEcho=2&iColumns=6&sColumns=%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=-1&mDataProp_0=0&sSearch_0=&bRegex_0=false&bSearchable_0=true&bSortable_0=true&mDataProp_1=1&sSearch_1=&bRegex_1=false&bSearchable_1=true&bSortable_1=true&mDataProp_2=2&sSearch_2=&bRegex_2=false&bSearchable_2=true&bSortable_2=true&mDataProp_3=3&sSearch_3=&bRegex_3=false&bSearchable_3=true&bSortable_3=true&mDataProp_4=4&sSearch_4=&bRegex_4=false&bSearchable_4=true&bSortable_4=true&mDataProp_5=5&sSearch_5=&bRegex_5=false&bSearchable_5=true&bSortable_5=true&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1"
URL_OTP_BASE = "http://51.89.99.105/NumberPanel/client/res/data_smscdr.php?fdate1=2025-12-11%2000:00:00&fdate2=2025-12-11%2023:59:59&frange=&fnum=&fcli=&fgdate=&fgmonth=&fgrange=&fgnumber=&fgcli=&fg=0&sesskey=Q05RRkJQUEJCVQ==&sEcho=2&iColumns=7&sColumns=%2C%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=-1&mDataProp_0=0&sSearch_0=&bRegex_0=false&bSearchable_0=true&bSortable_0=true&mDataProp_1=1&sSearch_1=&bRegex_1=false&bSearchable_1=true&bSortable_1=true&mDataProp_2=2&sSearch_2=&bRegex_2=false&bSearchable_2=true&bSortable_2=true&mDataProp_3=3&sSearch_3=&bRegex_3=false&bSearchable_3=true&bSortable_3=true&mDataProp_4=4&sSearch_4=&bRegex_4=false&bSearchable_4=true&bSortable_4=true&mDataProp_5=5&sSearch_5=&bRegex_5=false&bSearchable_5=true&bSortable_5=true&mDataProp_6=6&sSearch_6=&bRegex_6=false&bSearchable_6=true&bSortable_6=true&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/client/SMSCDRStats",
    "Origin": "http://51.89.99.105"
}

# گلوبل ویری ایبلز (Shared Memory)
class SessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.cookies.set("PHPSESSID", "jfogu3u27tvo7p2fdkt8tfs4k8") # Initial Cookie
        self.lock = threading.Lock()
        self.is_logging_in = False

    def get_timestamp(self):
        return int(time.time() * 1000)

    def login(self):
        with self.lock:
            if self.is_logging_in:
                return
            self.is_logging_in = True
        
        print("⚡ Background: Starting Login Process...")
        try:
            # Login Timeout 10s (Fast Fail)
            r1 = self.session.get(f"{BASE_URL}/login", timeout=10)
            match = re.search(r"What is (\d+) \+ (\d+) = \?", r1.text)
            
            if match:
                ans = int(match.group(1)) + int(match.group(2))
                payload = {
                    "username": CREDENTIALS["username"],
                    "password": CREDENTIALS["password"],
                    "capt": str(ans)
                }
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": f"{BASE_URL}/login"
                }
                self.session.post(f"{BASE_URL}/signin", data=payload, headers=headers, timeout=10)
                if "PHPSESSID" in self.session.cookies:
                    print("✅ Background: Login Successful")
                else:
                    print("❌ Background: Login Failed")
            else:
                print("❌ Background: Captcha Not Found")
        except Exception as e:
            print(f"⚠️ Background Login Error: {e}")
        finally:
            self.is_logging_in = False

    def keep_alive_loop(self):
        while True:
            try:
                # Check session validity
                ts = self.get_timestamp()
                check_url = f"{URL_OTP_BASE}&_={ts}"
                
                # Fast check (5s timeout)
                r = self.session.get(check_url, timeout=5)
                
                if "login" in r.text.lower() or "direct script" in r.text.lower():
                    print("⚠️ Session Expired. Re-logging immediately...")
                    self.login()
                else:
                    # Session is good
                    pass
            except:
                pass
            
            # 15 سیکنڈ کا وقفہ تاکہ سیشن فریش رہے
            time.sleep(15)

# Initialize Manager
manager = SessionManager()

# Start Background Thread
threading.Thread(target=manager.keep_alive_loop, daemon=True).start()

@app.route('/')
def home():
    return "⚡ High-Performance API Running on Gevent!"

@app.route('/api')
def handle_request():
    request_type = request.args.get('type')
    ts = manager.get_timestamp()
    
    target_url = ""
    if request_type == 'number':
        target_url = f"{URL_NUMBERS_BASE}&_={ts}"
    elif request_type == 'sms':
        target_url = f"{URL_OTP_BASE}&_={ts}"
    else:
        return jsonify({"error": "Invalid type"}), 400

    try:
        # Main request with 15s timeout
        # یہ ریکویسٹ لاگ ان نہیں کرے گی، صرف ڈیٹا لائے گی
        response = manager.session.get(target_url, timeout=15)
        
        # اگر ایچ ٹی ایم ایل آئے تو فوراً بیک گراؤنڈ لاگ ان ٹریگر کریں
        # لیکن یوزر کو ابھی ایرر دکھا دیں تاکہ ہینگ نہ ہو
        if "login" in response.text.lower():
            # Trigger background login asynchronously
            threading.Thread(target=manager.login).start()
            return jsonify({"status": "refreshing", "message": "Session refreshing, try again in 3 seconds"}), 503

        try:
            return jsonify(response.json())
        except:
            return response.text

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
