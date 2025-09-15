from flask import Flask, request, jsonify, render_template_string, Response
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from collections import Counter
import io
import openpyxl

app = Flask(__name__)

# 客户名称映射表
CUSTOMER_MAP = {
    "Lin Kee (Artane)": "五区",
    "Lin Kee (North Strand)": "三区",
    "Lin Kee (Glasnevin)": "九区",
    "Lin Kee (Swords)": "Swords",
    "Lin Kee (Cabra)": "七区"
}

# 首页界面
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
  button { background: black; color: white; border: none; border-radius: 6px; margin-top: 5px; }
  .card { background: #fff; padding: 15px; margin-top: 10px; border-radius: 10px;
          box-shadow: 0 2px 6px rgba(0,0,0,.1); }
</style>
</head>
<body>
  <h2>林记 · 订单助手</h2>
  <p>输入账号密码，一键获取订单（支持导出 Excel）</p>
  <input id="u" placeholder="用户名"><br>
  <input id="p" type="password" placeholder="密码"><br>
  <button onclick="fetchOrders()">获取订单</button>
  <button onclick="downloadExcel()">下载 Excel</button>
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

  // 显示汇总
  let html = '<div class="card"><h3>订单汇总</h3><ul>';
  for(const [store, count] of Object.entries(d.summary)){
    html += '<li>' + store + ': ' + count + ' 单</li>';
  }
  html += '</ul></div>';

  // 显示明细
  html += '<div class="card"><h3>订单明细</h3><ul>';
  for(const row of d.orders){
    html += '<li>客户: ' + row.Customer + ' | 订购日期: ' + row["Order Date"] + '</li>';
  }
  html += '</ul></div>';

  document.getElementById('res').innerHTML = html;
}

// 下载 Excel
function downloadExcel(){
  const u = document.getElementById('u').value;
  const p = document.getElementById('p').value;
  window.open('/export_excel?username='+encodeURIComponent(u)+'&password='+encodeURIComponent(p), '_blank');
}
</script>
</body>
</html>
    """)

# 抓取订单逻辑
def scrape_orders(username, password):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    rows = []
    try:
        driver.get("https://www.supplier.orderit.ie/#/login")
        wait = WebDriverWait(driver, 20)

        # 输入用户名
        username_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Username']")))
        username_input.click()
        username_input.send_keys(username)

        # 输入密码
        password_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Password']")))
        password_input.click()
        password_input.send_keys(password)

        # 点击登录
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button")))
        login_button.click()
        time.sleep(5)

        # 打开订单页面
        driver.get("https://www.supplier.orderit.ie/#/orders")
        time.sleep(5)

        # 提取订单表格
        table_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in table_rows:
            cols = [col.text.strip() for col in row.find_elements(By.TAG_NAME, "td")]
            if cols:
                customer_raw = cols[0] if len(cols) > 0 else ""
                order_date = cols[1] if len(cols) > 1 else ""
                customer = CUSTOMER_MAP.get(customer_raw, customer_raw)
                rows.append({"Customer": customer, "Order Date": order_date})

    finally:
        driver.quit()

    return rows

# 后端接口：获取 JSON
@app.route("/grab_orders", methods=["POST"])
def grab_orders():
    username = request.json.get("username")
    password = request.json.get("password")
    try:
        rows = scrape_orders(username, password)
        summary = dict(Counter([row["Customer"] for row in rows]))
        return jsonify({"status": "success", "orders": rows, "summary": summary})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

# 后端接口：导出 Excel
@app.route("/export_excel")
def export_excel():
    username = request.args.get("username")
    password = request.args.get("password")
    try:
        rows = scrape_orders(username, password)
        summary = dict(Counter([row["Customer"] for row in rows]))

        wb = openpyxl.Workbook()

        # 工作表 1：订单明细
        ws1 = wb.active
        ws1.title = "Orders"
        ws1.append(["Customer", "Order Date"])
        for row in rows:
            ws1.append([row["Customer"], row["Order Date"]])

        # 工作表 2：汇总统计
        ws2 = wb.create_sheet(title="Summary")
        ws2.append(["Customer", "订单数量"])
        for customer, count in summary.items():
            ws2.append([customer, count])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return Response(
            output.read(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment;filename=orders.xlsx"}
        )
    except Exception as e:
        return Response("Error: "+str(e), mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
