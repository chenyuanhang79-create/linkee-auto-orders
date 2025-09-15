from flask import Flask, request, jsonify, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

# 客户名称映射表
CUSTOMER_MAP = {
    "Lin Kee (Artane)": "五区",
    "Lin Kee (North Strand)": "三区",
    "Lin Kee (Glasnevin)": "九区",
    "Lin Kee (Swords)": "Swords",
    "Lin Kee (Cabra)": "七区"
}

# 首页：输入账号密码
@app.route("/")
def index():
    return render_template_string("""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>林记 · 订单助手</title>
<style>
  body { font-family: system-ui; padding: 20px; background: #f6f7f9; }
  input, button { padding: 10px; font-size: 16px; margin: 5px; width: 90%; }
  button { background: black; color: white; border: none; border-radius: 6px; }
  .card { background: #fff; padding: 15px; margin-top: 10px; border-radius: 10px;
          box-shadow: 0 2px 6px rgba(0,0,0,.1); }
</style>
</head>
<body>
  <h2>林记 · 订单助手</h2>
  <p>输入账号密码，一键获取订单（仅显示 客户 和 订购日期）</p>
  <input id="u" placeholder="用户名"><br>
  <input id="p" type="password" placeholder="密码"><br>
  <button onclick="fetchOrders()">获取订单</button>
  <div id="res"></div>

<script>
async function fetchOrders(){
  const u = document.getElementById('u').value;
  const p = document.getElementById('p').value;
  document.getElementById('res').innerHTML = '加载中...';
  const r = await fetch('/grab_orders', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({username:u, password:p})
  });
  const d = await r.json();
  if(d.status!=="success"){
    document.getElementById('res').innerHTML = '❌ 错误: ' + d.msg;
    return;
  }
  let html = '<div class="card"><h3>订单列表</h3><ul>';
  for(const row of d.orders){
    html += '<li>客户: ' + row.Customer + ' | 订购日期: ' + row["Order Date"] + '</li>';
  }
  html += '</ul></div>';
  document.getElementById('res').innerHTML = html;
}
</script>
</body>
</html>
    """)

# 后端接口：抓取订单
@app.route("/grab_orders", methods=["POST"])
def grab_orders():
    username = request.json.get("username")
    password = request.json.get("password")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 打开登录页
        driver.get("https://www.supplier.orderit.ie/#/login")
        time.sleep(3)

        # 登录
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Username']").send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button").click()
        time.sleep(5)

        # 跳转订单页
        driver.get("https://www.supplier.orderit.ie/#/orders")
        time.sleep(5)

        # 提取表格
        rows = []
        table_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in table_rows:
            cols = [col.text.strip() for col in row.find_elements(By.TAG_NAME, "td")]
            if cols:
                customer_raw = cols[0] if len(cols) > 0 else ""
                order_date = cols[1] if len(cols) > 1 else ""
                # 应用映射
                customer = CUSTOMER_MAP.get(customer_raw, customer_raw)
                rows.append({"Customer": customer, "Order Date": order_date})

        result = {"status": "success", "orders": rows}

    except Exception as e:
        result = {"status": "error", "msg": str(e)}

    finally:
        driver.quit()

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
