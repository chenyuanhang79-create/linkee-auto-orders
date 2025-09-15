from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Linkee Auto Orders Server Running!"

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
        driver.get("https://www.supplier.orderit.ie/#/dashboard")
        time.sleep(3)

        # 🔑 登录
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Username']").send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button").click()
        time.sleep(5)  # 等待页面加载

        # 🚚 跳转订单页
        driver.get("https://www.supplier.orderit.ie/#/orders")
        time.sleep(5)

        # 📊 提取表格
        rows = []
        table_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in table_rows:
            cols = [col.text.strip() for col in row.find_elements(By.TAG_NAME, "td")]
            if cols:
                rows.append(cols)

        result = {"status": "success", "orders": rows}

    except Exception as e:
        result = {"status": "error", "msg": str(e)}

    finally:
        driver.quit()

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
