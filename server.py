import os, re, time
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

# 商品映射（中英对照，可以自己补充）
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
async function fetchOrd
