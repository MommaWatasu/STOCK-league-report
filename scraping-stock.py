from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

import re
import time
from datetime import datetime
from bs4 import BeautifulSoup

import csv

def extract_value(html):
    """
    return  [日付, 始値, 高値, 安値, 終値, 出来高(売買高)]
    """
    soup = BeautifulSoup(html, "html.parser")
    graph = soup.find("div", class_="highcharts-tooltip")

    graph_td = graph.find_all("td")
    values = [datetime.strptime(graph_td[0].text, '%Y/%m/%d').date().strftime('%Y-%m-%d')]  # 日付格納
    for v in graph_td[1:]:
        if re.findall("始値|高値|安値|終値|売買高", v.text):
            values.append(re.sub(r'\D', "", v.text))

    return values

def scraping_stock_values(driver, url):
    stock_values = []

    driver.get(url)
    # ページの表示に時間がかかり取得できない場合を想定
    for _ in range(10):
        try:
            """
            graph_xy = driver.find_elements_by_class_name("highcharts-grid")
            print("graph_xy: ", graph_xy)
            """
            graph_xy = driver.find_elements(By.CLASS_NAME, "highcharts-grid")[1]  # graphの情報を取得
        except:
            print("continue find elements")
            continue
        break
    else:
        print("サイト構造の変化の可能性")
        raise
    g_w = int(graph_xy.rect['width'])
    # 中心にいる→中心からグラフ幅の右半分移動(最新の株価)
    actions = ActionChains(driver)
    # NOTE: move_to_element_with_offsetだとうまくいかない
    actions.move_to_element(graph_xy).perform()
    actions.move_by_offset(g_w // 2, 0).perform()
    html = driver.page_source.encode('utf-8')
    stock_values.append(extract_value(html))
    for _ in range(g_w-1):
        actions = ActionChains(driver)
        # 左に一つ移動
        actions.move_by_offset(-1, 0).perform()
        html = driver.page_source.encode('utf-8')
        tmp_value = extract_value(html)
        if tmp_value not in stock_values:
            stock_values.append(tmp_value)
            print("get new data")

    return stock_values

def get_data(code, name):
    type_ = "6month"
    url = f"https://www.nikkei.com/nkd/company/chart/?type={type_}&scode={code}"

    options = Options()
    # Headlessモードを有効にする（コメントアウトするとブラウザが実際に立ち上がります）
    options.headless = True
    # ブラウザを起動する
    driver = webdriver.Firefox(options=options)
    start = time.time()
    result = scraping_stock_values(driver, url)
    print(f"scraping {name} in:{time.time()-start}")
    print("saving results")
    with open("/home/watasu/HorseMLdatasets/stock/{}.csv".format(name), "a") as f:
        writer = csv.writer(f)
        for data in result:
            writer.writerow(data)

    driver.close()
    driver.quit()
    return

if __name__ == "__main__":
    stocks = [(6502, "東芝"), (6804, "ホシデン"), (7752, "リコー"), (6752, "パナソニック"), (5711, "三菱マテリアル"), (4901, "富士フィルムホールディングス"), (4237, "フジプレミアム")]
    try:
        #最初に一行空行を入れる
        with open("/home/watasu/HorseMLdatasets/stock/{}.csv".format(name), "a") as f:
            writer = csv.writer(f)
            writer.writerow([])
    except:
        #もしファイルが存在しなければ、ファイルを生成しておく
        with open("/home/watasu/HorseMLdatasets/stock/{}.csv".format(name), "w") as f:
    for (code, name) in stocks:
        get_data(code, name)
    print("complete scraping!")