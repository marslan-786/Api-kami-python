import threading
import time
import requests
import re
import os
import logging
from flask import Flask, request, Response, stream_with_context
from gevent.pywsgi import WSGIServer

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

COOKIE_FILE = "session_cookie.txt"

class SessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.lock = threading.Lock()
        self.last_login_time = 0
        self.load_cookie_from_file()

    def get_timestamp(self):
        return int(time.time() * 1000)

    def save_cookie_to_file(self, cookie_value):
        try:
            with open(COOKIE_FILE, "w") as f:
                f.write(cookie_value)
        except:
            pass

    def load_cookie_from_file(self):
        try:
            if os.path.exists(COOKIE_FILE):
                with open(COOKIE_FILE, "r") as f:
                    cookie = f.read().strip()
                    if cookie:
                        self.session.cookies.set("PHPSESSID", cookie)
            else:
                self.session.cookies.set("PHPSESSID", "jfogu3u27tvo7p2fdkt8tfs4k8")
        except:
            pass

    def login(self):
        with self.lock:
            if time.time() - self.last_login_time < 30:
                return

            print("⚡ System: Starting Login Process...")
            try:
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
                        new_cookie = self.session.cookies["PHPSESSID"]
                        print(f"✅ Login Successful! New Cookie: {new_cookie}")
                        self.save_cookie_to_file(new_cookie)
                        self.last_login_time = time.time()
            except Exception as e:
                print(f"⚠️ Login Error: {e}")

    def keep_alive_loop(self):
        while True:
            try:
                ts = self.get_timestamp()
                check_url = f"{URL_OTP_BASE}&_={ts}"
                # Just fetch headers to verify session (efficient)
                r = self.session.get(check_url, timeout=10, stream=True)
                chunk = next(r.iter_content(chunk_size=1024), b"")
                r.close()
                
                if b"login" in chunk.lower() or b"direct script" in chunk.lower():
                    print("⚠️ Background: Session Dead. Logging in...")
                    self.login()
            except:
                pass
            time.sleep(40)

manager = SessionManager()
threading.Thread(target=manager.keep_alive_loop, daemon=True).start()

@app.route('/')
def home():
    return "🚀 Rocket Mode: Direct Pass-Through Active!"

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
        return Response("Error: Invalid type", status=400)

    try:
        # stream=True کا مطلب ہے ڈیٹا کو میموری میں روکے بغیر آگے بھیجو
        upstream_req = manager.session.get(target_url, stream=True, timeout=25)
        
        # رسپانس ہیڈرز چیک کریں کہ JSON ہے یا HTML
        c_type = upstream_req.headers.get('Content-Type', '')

        # اگر HTML ہے (مطلب لاگ ان پیج یا ایرر)
        if 'text/html' in c_type:
            # تھوڑا سا ڈیٹا پڑھ کر کنفرم کریں
            chunk = next(upstream_req.iter_content(chunk_size=1024), b"")
            if b"login" in chunk.lower() or b"Direct Script" in chunk:
                print("⚠️ Request: Session expired. Refreshing...")
                upstream_req.close()
                manager.login()
                # دوبارہ ٹرائی کریں
                upstream_req = manager.session.get(target_url, stream=True, timeout=25)
            else:
                # اگر کوئی اور ایچ ٹی ایم ایل ایرر ہے تو وہی دکھا دیں
                return Response(chunk, status=upstream_req.status_code)

        # 🚀 THE MAGIC: Direct Streaming
        # ہم ڈیٹا کو variable میں اسٹور نہیں کر رہے، سیدھا آگے بھیج رہے ہیں
        return Response(
            stream_with_context(upstream_req.iter_content(chunk_size=8192)),
            content_type=upstream_req.headers.get('Content-Type'),
            status=upstream_req.status_code
        )

    except Exception as e:
        return Response(str(e), status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    http_server = WSGIServer(('0.0.0.0', port), app)
    http_server.serve_forever()
