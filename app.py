import os
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase 初始化邏輯
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>魏郁倫的電影系統</h1><a href='/spidermovie'>1. 執行爬蟲</a> | <a href='/searchMovie'>2. 搜尋電影</a>"

# (1) 爬取並存到資料庫
@app.route("/spidermovie")
def spidermovie():
    url = "http://www.atmovies.com.tw/movie/next/"
    data = requests.get(url)
    data.encoding = "utf-8"
    sp = BeautifulSoup(data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間：","")
    
    result = sp.select(".filmListAllX li")
    total = 0
    for item in result:
        total += 1
        movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
        title = item.find(class_="filmtitle").text
        picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
        hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")
        showDate = item.find(class_="runtime").text[5:15]

        doc = {"title": title, "picture": picture, "hyperlink": hyperlink, "showDate": showDate}
        db.collection("電影2B").document(movie_id).set(doc)

    return f"網站最新更新日期: {lastUpdate}<br>總共爬取 {total} 部電影到資料庫<br><a href='/'>返回</a>"

# (2) 搜尋資料庫
@app.route("/searchMovie")
def searchMovie():
    keyword = request.args.get("keyword", "")
    R = "<h2>搜尋電影</h2><form action='/searchMovie' method='GET'>"
    R += f"關鍵字: <input type='text' name='keyword' value='{keyword}'>"
    R += "<input type='submit' value='查詢'></form><hr>"

    if keyword:
        docs = db.collection("電影2B").stream()
        for doc in docs:
            m = doc.to_dict()
            if keyword.lower() in m.get("title", "").lower():
                R += f"<b>編號:</b> {doc.id}<br><b>片名:</b> {m.get('title')}<br>"
                R += f"<b>上映日期:</b> {m.get('showDate')}<br>"
                R += f"<a href='{m.get('hyperlink')}'>電影介紹頁</a><br>"
                R += f"<img src='{m.get('picture')}' width='150'><hr>"
    return R + "<a href='/'>返回</a>"

if __name__ == "__main__":
    app.run()
