from flask import Flask, request, jsonify, render_template_string, Response
import requests
import io
import openpyxl
from collections import Counter

app = Flask(__name__)

CUSTOMER_MAP = {
    "Lin Kee (Artane)": "五区",
    "Lin Kee (North Strand)": "三区",
    "Lin Kee (Glasnevin)": "九区",
    "Lin Kee (Swords)": "Swords",
    "Lin Kee (Cabra)": "七区"
}

API_URL = "https://api.supplier.orderit.ie/api/c-r-m/customer/lists"

# 首页
@app.route("/")
def index():
    return render_template_string("""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>林记 · 订单助手 (API版)</title>
<style>
  body { font-family: system-ui; padding: 20px; background: #f6f7f9; }
  input, button { padding: 10px; font-size: 16px; margin: 5px; width: 90%; }
  button { background: black; color: white; border: none; border-radius: 6px; margin-top: 5px; }
  .card { background: #fff; padding: 15px; margin-top: 10px; border-radius: 10px;
          box-shadow: 0 2px 6px rgba(0,0,0,.1); }
</style>
</head>
<body>
  <h2>林记 · 订单助手 (API版)</h2>
  <p>输入 Bearer Token（先从 F12 → Network → XHR → lists 里复制）</p>
  <input id="token" placeholder="Bearer xxx"><br>
  <button onclick="fetchOrders()">获取订单</button>
  <button onclick="downloadExcel()">下载 Excel</button>
  <div id="res"></div>
<script>
async function fetchOrders(){
  const t = document.getElementById('token').value;
  document.getElementById('res').innerHTML = '加载中...';
  const r = await fetch('/grab_orders', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({token:t})
  });
  const d = await r.json();
  if(d.status!=="success"){
    document.getElementById('res').innerHTML = '❌ 错误: ' + d.msg;
    return;
  }
  let html = '<div class="card"><h3>订单汇总</h3><ul>';
  for(const [store, count] of Object.entries(d.summary)){
    html += '<li>' + store + ': ' + count + ' 单</li>';
  }
  html += '</ul></div>';
  html += '<div class="card"><h3>订单明细</h3><ul>';
  for(const row of d.orders){
    html += '<li>客户: ' + row.Customer + ' | 订购日期: ' + row["Order Date"] + '</li>';
  }
  html += '</ul></div>';
  document.getElementById('res').innerHTML = html;
}
function downloadExcel(){
  const t = document.getElementById('token').value;
  window.open('/export_excel?token='+encodeURIComponent(t), '_blank');
}
</script>
</body>
</html>
""")

# 获取订单
def get_orders(token):
    headers = {
        "Authorization": token,
        "company-id": "2",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {"pageNum": 1, "pageSize": 100}
    res = requests.post(API_URL, headers=headers, json=payload)
    data = res.json()

    orders = []
    for item in data.get("data", {}).get("list", []):
        customer_raw = item.get("customerName")
        order_date = item.get("orderDate")
        customer = CUSTOMER_MAP.get(customer_raw, customer_raw)
        orders.append({"Customer": customer, "Order Date": order_date})
    return orders

@app.route("/grab_orders", methods=["POST"])
def grab_orders():
    token = request.json.get("token")
    try:
        rows = get_orders(token)
        summary = dict(Counter([row["Customer"] for row in rows]))
        return jsonify({"status": "success", "orders": rows, "summary": summary})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route("/export_excel")
def export_excel():
    token = request.args.get("token")
    try:
        rows = get_orders(token)
        summary = dict(Counter([row["Customer"] for row in rows]))
        wb = openpyxl.Workbook()

        ws1 = wb.active
        ws1.title = "Orders"
        ws1.append(["Customer", "Order Date"])
        for row in rows:
            ws1.append([row["Customer"], row["Order Date"]])

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
