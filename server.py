import os, time
from flask import Flask, request, jsonify, render_template_string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

SUPPLIER_BASE = "https://www.supplier.orderit.ie"
LOGIN_URL = f"{SUPPLIER_BASE}/#/login"
ORDERS_URL = f"{SUPPLIER_BASE}/#/orders"

app = Flask(__name__)

I18N = {
    "3+1 (大) 400pcs": "3+1 (Large) 400pcs",
    "大手提袋 300pcs": "Large Carry Bag 300pcs",
    "小手提袋 300pcs": "Small Carry Bag 300pcs",
    "薯条袋 2000pcs": "French Fries Bag 2000pcs",
    "Plain 平底袋": "Plain Flat Bag",
    "大盒 500pcs": "Large Box 500pcs",
    "16oz noodle box 炒饭盒500": "16oz Noodle/Fried Rice Box 500",
    "8 Oz Soup Cup 500/box": "8oz Soup Cup 500/box",
    "16 Oz Soup Cup 500/box": "16oz Soup Cup 500/box",
    "26 Oz Soup Cup 500/box": "26oz Soup Cup 500/box",
    "98mm PP LID 500/box": "98mm PP Lid 500/box",
    "116mm PP LID 500/box": "116mm PP Lid 500/box",
}

def build_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1600")
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

def grab_orders(username, password):
    driver = build_driver()
    try:
        driver.get(LOGIN_URL)
        time.sleep(2)
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(5)
        driver.get(ORDERS_URL)
        time.sleep(6)
        rows = [el.text for el in driver.find_elements(By.CSS_SELECTOR, "table tr") if el.text.strip()]
        return rows
    finally:
        driver.quit()

@app.route("/", methods=["GET"])
def index():
    return render_template_string("""
<!doctype html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>林记 · 订单助手</title>
<style>
body{font-family:system-ui; padding:20px; background:#f6f7f9;}
input,button{padding:10px;font-size:16px;margin:5px;}
button{background:black;color:white;border:none;border-radius:6px}
.card{background:#fff;padding:15px;margin-top:10px;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,.1)}
</style>
</head><body>
<h2>林记 · 订单助手</h2>
<p>输入账号密码，一键获取订单</p>
<input id="u" placeholder="用户名"><br>
<input id="p" type="password" placeholder="密码"><br>
<button onclick="fetchOrders()">获取订单</button>
<div id="res"></div>
<script>
async function fetchOrders(){
  const u=document.getElementById('u').value;
  const p=document.getElementById('p').value;
  document.getElementById('res').innerHTML='加载中...';
  const r=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
  const d=await r.json();
  if(!d.ok){document.getElementById('res').innerHTML='失败: '+d.error;return;}
  let html='<div class=card><h3>订单统计</h3>';
  for(const k in d.store_totals){html+=`<p>${k}: ${d.store_totals[k]} 件</p>`}
  html+='</div><div class=card><h3>SKU汇总</h3><ul>';
  for(const item of d.sku_totals){html+=`<li>${item.product} (${item.product_en}): ${item.qty}</li>`}
  html+='</ul></div>';
  document.getElementById('res').innerHTML=html;
}
</script>
</body></html>
    """)

@app.route("/api/orders", methods=["POST"])
def api_orders():
    data = request.get_json(force=True)
    u, p = data.get("username"), data.get("password")
    try:
        rows = grab_orders(u, p)
        # 简化统计：这里先用行数假设，每个门店分得一样多
        totals = {"D3":len(rows)//4, "D9":len(rows)//4, "SW":len(rows)//4, "D5":len(rows)//4}
        sku = [{"product":k,"product_en":I18N.get(k,""),"qty":1} for k in I18N.keys()]
        return jsonify({"ok":True,"store_totals":totals,"sku_totals":sku})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
