# coding=UTF-8
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from flask import render_template, flash, redirect, url_for, request, jsonify, send_file, escape, send_from_directory
from flask_paginate import Pagination, get_page_args
from datetime import datetime as dt
import datetime
from db import query_handle
import json
# from pymysql import escape_string

import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import numpy as np
import threading
import urllib.parse as urlparse
from urllib.parse import parse_qs

def order_page(page=1,now=''):
    # Setting page, limit and offset variables
    per_page = 60
    offset = (page-1) * per_page

    # Executing a query to get the first data of products
    query =  "SELECT purchase_date FROM orders ORDER BY purchase_date DESC LIMIT 1;"
    db, cursor = query_handle(query)
    first_data = cursor.fetchall()

    if request.args.get('startdate'):
        start = request.args.get('startdate')
        end = request.args.get('enddate')
        ISOTIMEFORMAT = '%Y-%m-%d'
        start = dt.strptime(start,ISOTIMEFORMAT).replace(hour=00, minute=00)
        end = dt.strptime(end,ISOTIMEFORMAT).replace(hour=23, minute=59)

        # 最前面不用加空格，最後面要加空格
        other_filter = ''

        if request.args.get('brand'):
            brand = request.args.get('brand')
            other_filter = "{0} AND SUBSTRING(SKU, 1, 1)='{1}' ".format(other_filter, brand)
        if request.args.get('money_status'):
            money_status_index = request.args.get('money_status')
            money_status = ''
            if money_status_index == '1':
                money_status = '未付款'
            elif money_status_index == '2':
                money_status = '已付款'
            elif money_status_index == '3':
                money_status = '已轉帳'
            other_filter = "{0} AND money_status like '%{1}%' ".format(other_filter, money_status)
        if request.args.get('order_status'):
            order_status_index = request.args.get('order_status')
            order_status = ''
            if order_status_index == '1':
                order_status = '待處理'
            elif order_status_index == '2':
                order_status = '已配送'
            elif order_status_index == '3':
                order_status = '已完成'
            elif order_status_index == '4':
                order_status = '已取消'
            other_filter = "{0} AND order_status = '{1}' ".format(other_filter, order_status)
        if request.args.get('payment_way'):
            payment_way_index = request.args.get('payment_way')
            payment_way = ''
            if payment_way_index == '1':
                payment_way = '到宅付款'
            elif payment_way_index == '2':
                payment_way = '信用卡'
            elif payment_way_index == '3':
                payment_way = 'ATM'
            elif payment_way_index == '4':
                payment_way = '超商代碼'
            other_filter = "{0} AND payment_way like '%{1}%' ".format(other_filter, payment_way)
        if request.args.get('order_id'):
            order_id = request.args.get('order_id')
            other_filter = "{0} AND OID like '%{1}%' ".format(other_filter, order_id)
        if request.args.get('product'):
            product = request.args.get('product')
            other_filter = "{0} AND product like '%{1}%' ".format(other_filter, product)
        if request.args.get('sku'):
            sku = request.args.get('sku')
            other_filter = "{0} AND SKU like '%{1}%' ".format(other_filter, sku)
        if request.args.get('utm_source'):
            utm_source = request.args.get('utm_source')
            other_filter = "{0} AND utm_source like '%{1}%' ".format(other_filter, utm_source)


        query_total = "SELECT * FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') {2} ORDER BY purchase_date DESC;" .format(start, end, other_filter)
        query_pag = "SELECT * FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') {2} ORDER BY purchase_date DESC LIMIT {3} OFFSET {4} ;" .format(start, end, other_filter, per_page, offset)

    else:
        query_total =  "SELECT * FROM orders ORDER BY purchase_date DESC;"
        query_pag = "SELECT * FROM orders ORDER BY purchase_date DESC LIMIT %s OFFSET %s ;" %(per_page, offset)

    # Executing a query to get the total number of products
    db, cursor = query_handle(query_total)
    global total
    total = cursor.fetchall()

    # Executing a query with LIMIT and OFFSET provided by the variables above
    db, cursor = query_handle(query_pag)
    orders = cursor.fetchall()

    # Closing cursor
    cursor.close()

    # Setting up the pagination variable
    pagination = Pagination(page=page, per_page=per_page, offset=offset, total=len(total), record_name='orders', css_framework='bootstrap3')

    db.close()
    if first_data:
        update = request.args.get('update') or  first_data[0][0]
    else:
        update='No data'
    return render_template('order.html', orders=orders, pagination=pagination, newest_date=update)


def report():
    df = pd.DataFrame(total, columns=['商品', 'SKU', '數量', '單價', '總計', '商品小計', '訂單ID', 'utm_source', '會員', '會員群組', '購買人', '電話', 'E-Mail', '金額', '匯款狀態', '訂單狀態', '付款方式', '配送方式', 'IP位址', '瀏覽系統', '購買日期', '上次購買日期', '修改日期', '購買人 - 聯絡地址', '備註','id','會員ID'])
    df.drop(['id'], axis=1, inplace=True)
    df['總計'] = df['總計'].apply(lambda x : int(x.replace('$','').replace(',','')))
    df.loc['總金額','總計'] = df.loc[:,'總計'].sum()
    df.loc['總金額'] = df.loc['總金額'].fillna('')
    df.to_csv('filter_order.csv')
    return redirect(url_for('report_download'))


def report_download():
    return send_file("filter_order.csv",as_attachment=True, cache_timeout=0)

def order_crawler():
    ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'
    now = datetime.datetime.now().strftime(ISOTIMEFORMAT)

    # 每天凌晨兩點更新最近20天的數據
    timer = threading.Timer(86400, order_crawler)
    timer.start()

    now_time = datetime.datetime.now().replace(hour=23,minute=59,second=59)
    past_time = (datetime.datetime.now() - datetime.timedelta(days=19)).replace(hour=00,minute=00,second=00)
    
    ISODATEFORMAT = '%Y-%m-%d'
    now_date = now_time.strftime(ISODATEFORMAT)
    past_date = past_time.strftime(ISODATEFORMAT)
    
    # 刪掉20天的數據
    query = "DELETE FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}')".format(past_time, now_time)
    db, cursor = query_handle(query)
    db.commit()
    db.close()

    # 刪掉全部數據
    # query = "truncate table orders;"
    # db, cursor = query_handle(query)
    # db.commit()
    # db.close()

    cap = DesiredCapabilities().CHROME
    cap["marionette"] = False
    browser =  webdriver.Remote(
                command_executor=CHROMEDRIVER_ADDRESS,
                desired_capabilities=cap)
    browser.maximize_window()  # 最大化視窗
    wait = WebDriverWait(browser, 10) # 等待載入10s


    LOGIN_URL = LOGIN_URL
    #get token
    res = requests.get(LOGIN_URL).text
    html = BeautifulSoup(res,"html.parser")
    token = html.find_all(type="hidden")[1]["value"]

    URL = ORDER_URL + '&token='+token+'&filter_date_added_start='+past_date+'&filter_date_added_end='+now_date+'&page=1'

    browser.get(URL)
    browser.execute_script("document.getElementById('username').value='ACCOUNT'")
    browser.execute_script("document.getElementById('password').value='PASSWORD'")
    browser.execute_script("document.getElementById('btn-login').click()")
    time.sleep(5)
    df = pd.DataFrame()

    while True: #全部頁數
        time.sleep(2) #載入訂單列表
        soup = BeautifulSoup(browser.page_source,"html.parser")
        order_list = soup.find_all("tr",attrs = {"class":"order-list-row"})
        c_url = urlparse.urlparse(browser.current_url)
        print ("page {} start".format(parse_qs(c_url.query)['page'][0]))
        for ti,order in enumerate(order_list): #1頁60筆
            print(order.attrs['data-order-id'])
            for i in range(10):
                if i >= 9 :               
                    print("id timeout")  # 嘗試超過10次 print timeout
                    break
                try:
                    id = browser.find_element_by_xpath("//u[contains(text(), '"+ order.attrs['data-order-id'] + "')]")
                    if id:
                        for i in range(20):
                            if i >= 19 :               
                                print("click order id timeout")  # 嘗試超過20次 print timeout
                                raise Exception
                            try:
                                id.click()
                                #避免沒有click進info頁面中
                                if 'info' in browser.current_url:
                                    break
                                else:
                                    raise Exception
                            except:
                                print('click order id again')
                                time.sleep(2)
                        break
                    else:
                        raise Exception
                except:
                    print('try order id again')
                    time.sleep(2)
            content = BeautifulSoup(browser.page_source,"html.parser")
            # tidy
            # product_block
            product_block = content.find("div",attrs = {"id":"tab-product"})
            all_col_arr = []
            all_val_arr = []
            # title
            try:
                product_title = product_block.find('thead').find_all('td')
            except:
                for i in range(10):
                    if i >= 9 :               
                        print("product block timeout")  # 嘗試超過20次 print timeout
                        break
                    try:
                        content = BeautifulSoup(browser.page_source,"html.parser")
                        product_block = content.find("div",attrs = {"id":"tab-product"})
                        product_title = product_block.find('thead').find_all('td')
                        break
                    except:
                        print('try product block again')
                        time.sleep(2)
                # 預防增加訂單時導致的id因為換頁而讀不到的問題
                if product_block:
                    pass
                else:
                    c_url = browser.current_url
                    if 'info' in c_url:
                        browser.back() #若是停留在info介面要再回前一頁
                        continue #繼續下一筆
                    else:
                        print(c_url)
                        print('test stop reason')
                        break
            for title in product_title[2:]:
                all_col_arr.append(title.get_text())
            all_col_arr.append('商品小計')
            # value
            product_block_info = product_block.find_all('tbody')
            product_block_purchase_catnum = len(product_block_info[0].find_all('tr')) #買了幾項產品
            product_block_purchase = product_block_info[0].find_all('tr')
            val_arr = [[] for j in range(product_block_purchase_catnum)]
            for ix,val in enumerate(product_block_purchase):
                val_arr[ix].append(val.find('a').get_text()) #商品名
                product_list = val.find_all('td')
                for product in product_list[3:]:
                    val_arr[ix].append(product.get_text()) #sku,數量,單價,總計
            total = product_block_info[1].find_all('td')[3].get_text() # 商品小計
            all_val_arr.append(total)
            # 贈品
            gifts_num = 0
            if len(product_block.find_all('table')) > 1:
                gifts = product_block.find_all('table')[1].find('tbody').find_all('tr')
                gifts_num = len(gifts)
                val_arr.extend([] for j in range(gifts_num))
                for i,gift in enumerate(gifts):
                    gift_list = gift.find_all('td')[1:]
                    for gval in gift_list:
                        val_arr[product_block_purchase_catnum+i].append(gval.get_text()) #商品名,sku,數量
                    val_arr[product_block_purchase_catnum+i].extend(["$0","$0"])

            # order block
            order_block = content.find("div",attrs = {"id":"tab-order"})
            td_list = order_block.find_all('td')
            getMID = False
            for ii,info in enumerate(td_list):
                if ii%2==0:
                    all_col_arr.append(info.get_text())
                    if info.get_text()=="會員":
                        getMID = True
                        all_col_arr.append("會員ID")
                else:
                    all_val_arr.append(info.get_text())
                    if getMID:
                        mid = info.find('a').get('href').split('customer_id=')[1]
                        all_val_arr.append(mid)
                        getMID = False

            # combine all
            for ci in range(product_block_purchase_catnum + gifts_num):
                val_arr[ci].extend(all_val_arr)
                new_df = pd.DataFrame([val_arr[ci]], columns=all_col_arr)

                # 因為每筆訂單擁有的維度都不同，有些會漏聯絡地址、備註等等，因此用model_df來設定維度，讓每筆訂單有的欄位都相同
                model_df = pd.DataFrame(columns=['商品', 'SKU', '數量', '單價', '總計', '商品小計', '訂單ID', 'utm_source', '會員','會員ID'
       '會員群組', '購買人', '購買人 - 聯絡地址', '電話', 'E-Mail', '金額', '匯款狀態', '訂單狀態', '付款方式', '配送方式', '備註',
       'IP位址', '瀏覽系統', '購買日期', '上次購買日期', '修改日期'])
                # new_df的維度未整理過，model_df設定固定維度，order_df根據固定維度作統一模式
                order_df = new_df.append(model_df)
                # put order in db
                v = order_df.loc[0]
                query = 'INSERT INTO orders(product, SKU, quantity, price, sum, total, OID, utm_source, member, MID, member_group, user, phone, email, amount, money_status, order_status, payment_way, delivery_way, IP, browser, purchase_date, last_purchase_date, updated_date, contact_address, remarks) VALUES("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}");'.format(v['商品'],v['SKU'],v['數量'],v['單價'],v['總計'],v['商品小計'],v['訂單ID'],v['utm_source'],escape(str(v['會員'])),v['會員ID'],v['會員群組'],escape(str(v['購買人'])),v['電話'],v['E-Mail'],v['金額'],v['匯款狀態'],v['訂單狀態'],v['付款方式'],v['配送方式'],v['IP位址'],v['瀏覽系統'],v['購買日期'],v['上次購買日期'],v['修改日期'],v['購買人 - 聯絡地址'],escape(str(v['備註'])))
                db, cursor = query_handle(query)
                db.commit()
                db.close()
            # 前往下一個訂單編號
            browser.back()

        try:
            c_url = urlparse.urlparse(browser.current_url)
            now_page = parse_qs(c_url.query)['page'][0]
            print ("page {} end".format(now_page))
            for i in range(10):
                if i >= 9 :               
                    print("next page timeout")  # 嘗試超過10次 print timeout
                    raise Exception
                try:
                    next = browser.find_element_by_xpath("//div[@class='links']/a[contains(text(), '›')]")
                    if next:
                        for i in range(20):
                            if i >= 19 :               
                                print("click next page timeout")  # 嘗試超過20次 print timeout
                                raise Exception
                            try:
                                next.click()
                                #避免沒有點進下一頁
                                c_url = urlparse.urlparse(browser.current_url)
                                if "info" in browser.current_url:
                                    print("in info")
                                    print (browser.current_url)
                                    browser.back()
                                    raise Exception
                                elif int(parse_qs(c_url.query)['page'][0]) == (int(now_page)+1):
                                    break #有實際到下一頁
                                else:
                                    raise Exception
                            except:
                                print('click next again')
                                time.sleep(2)       
                        break
                    else:
                        raise Exception
                except:
                    print('try next again')
                    time.sleep(2)
        except:
            print('finish!')
            # 刪掉處理過久的重複值
            query = 'DELETE FROM orders WHERE (OID,product) IN (SELECT OID,product FROM (select OID,product from orders group by OID,product having count(*)>1) e) AND id NOT IN (SELECT id FROM (SELECT MIN(id) AS id from orders group by OID,product having count(*)>1) t);'
            db, cursor = query_handle(query)
            db.commit()
            db.close()
            return redirect(url_for('order_page',update=now))
            break

# 設定 schedule 及執行
# 獲取現在時間
sched_now_time = datetime.datetime.now()
# 獲取明天時間
sched_next_time = sched_now_time + datetime.timedelta(days=+1)
sched_next_year = sched_next_time.date().year
sched_next_month = sched_next_time.date().month
sched_next_day = sched_next_time.date().day
# 獲取明天2點時間
sched_next_time = datetime.datetime.strptime(str(sched_next_year)+"-"+str(sched_next_month)+"-"+str(sched_next_day)+" 02:00:00", "%Y-%m-%d %H:%M:%S")

# 獲取距離明天2點時間，單位為秒
timer_start_time = (sched_next_time - sched_now_time).total_seconds()

# 定時器,參數為(多少時間後執行，單位為秒，執行的方法)
timer = threading.Timer(timer_start_time, order_crawler)
print("Order Timer go")
timer.start()
    

    