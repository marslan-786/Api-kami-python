import threading
import time
import requests
import re
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

CREDENTIALS = {
    "username": "Kami522",
    "password": "Kami526"
}

BASE_URL = "http://51.89.99.105/NumberPanel"

# 👇 لنکس سے پرانا ٹائم اسٹیمپ (_=1765...) ہٹا دیا گیا ہے
URL_NUMBERS_BASE = "http://51.89.99.105/NumberPanel/client/res/data_smsnumbers.php?frange=&fclient=&sEcho=2&iColumns=6&sColumns=%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=-1&mDataProp_0=0&sSearch_0=&bRegex_0=false&bSearchable_0=true&bSortable_0=true&mDataProp_1=1&sSearch_1=&bRegex_1=false&bSearchable_1=true&bSortable_1=true&mDataProp_2=2&sSearch_2=&bRegex_2=false&bSearchable_2=true&bSortable_2=true&mDataProp_3=3&sSearch_3=&bRegex_3=false&bSearchable_3=true&bSortable_3=true&mDataProp_4=4&sSearch_4=&bRegex_4=false&bSearchable_4=true&bSortable_4=true&mDataProp_5=5&sSearch_5=&bRegex_5=false&bSearchable_5=true&bSortable_5=true&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1"
URL_OTP_BASE = "http://51.89.99.105/NumberPanel/client/res/data_smscdr.php?fdate1=2025-12-11%2000:00:00&fdate2=2025-12-11%2023:59:59&frange=&fnum=&fcli=&fgdate=&fgmonth=&fgrange=&fgnumber=&fgcli=&fg=0&sesskey=Q05RRkJQUEJCVQ==&sEcho=2&iColumns=7&sColumns=%2C%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=-1&mDataProp_0=0&sSearch_0=&bRegex_0=false&bSearchable_0=true&bSortable_0=true&mDataProp_1=1&sSearch_1=&bRegex_1=false&bSearchable_1=true&bSortable_1=true&mDataProp_2=2&sSearch_2=&bRegex_2=false&bSearchable_2=true&bSortable_2=true&mDataProp_3=3&sSearch_3=&bRegex_3=false&bSearchable_3=true&bSortable_3=true&mDataProp_4=4&sSearch_4=&bRegex_4=false&bSearchable_4=true&bSortable_4=true&mDataProp_5=5&sSearch_5=&bRegex_5=false&bSearchable_5=true&bSortable_5=true&mDataProp_6=6&sSearch_6=&bRegex_6=false&bSearchable_6=true&bSortable_6=true&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/client/SMSCDRStats",
    "Origin": "http://51.89.99.105"
}

client = requests.Session()
client.headers.update(HEADERS)

# Initial Cookie set
client.cookies.set("PHPSESSID", "jfogu3u27tvo7p2fdkt8tfs4k8")

def get_timestamp():
    """ملی سیکنڈز میں موجودہ وقت نکالنے کا فنکشن"""
    return int(time.time() * 1000)

def perform_login():
    try:
        r1 = client.get(f"{BASE_URL}/login")
        match = re.search(r"What is (\d+) \+ (\d+) = \?", r1.text)
        if not match:
            return False
            
        ans = int(match.group(1)) + int(match.group(2))
        
        payload = {
            "username": CREDENTIALS["username"],
            "password": CREDENTIALS["password"],
            "capt": str(ans)
        }
        
        post_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{BASE_URL}/login"
        }
        
        client.post(f"{BASE_URL}/signin", data=payload, headers=post_headers)
        
        if "PHPSESSID" in client.cookies:
            return True
        else:
            return False
    except:
        return False

def keep_alive():
    while True:
        try:
            if "PHPSESSID" not in client.cookies:
                perform_login()
            else:
                # Keep alive request with timestamp
                ts = get_timestamp()
                # ہم ڈیش بورڈ کے بجائے سیدھا OTP پیج کو پنگ کرتے ہیں تاکہ سیشن ایکٹو رہے
                ping_url = f"{URL_OTP_BASE}&_={ts}"
                r = client.get(ping_url)
                
                if "login" in r.text.lower():
                    perform_login()
        except:
            pass
        time.sleep(30)

threading.Thread(target=keep_alive, daemon=True).start()

@app.route('/')
def home():
    return "Railway API is Running!"

@app.route('/api')
def handle_request():
    request_type = request.args.get('type')
    
    # یہاں ہم لنک میں ٹائم اسٹیمپ جوڑ رہے ہیں
    current_time = get_timestamp()
    
    target_url = ""
    if request_type == 'number':
        target_url = f"{URL_NUMBERS_BASE}&_={current_time}"
    elif request_type == 'sms':
        target_url = f"{URL_OTP_BASE}&_={current_time}"
    else:
        return jsonify({"error": "Invalid type. Use ?type=number or ?type=sms"}), 400

    try:
        response = client.get(target_url)
        
        if "login" in response.text.lower():
            perform_login()
            response = client.get(target_url)

        try:
            return jsonify(response.json())
        except:
            return response.text
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
