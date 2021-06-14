# coding=UTF-8
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from flask import render_template, flash, redirect, url_for, request, jsonify, send_file, escape
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
import re
import threading
import urllib.parse as urlparse
from urllib.parse import parse_qs

def member_page(page=1,now=''):
    # Setting page, limit and offset variables
    per_page = 40
    offset = (page-1) * per_page

    # Executing a query to get the first data of members
    query =  "SELECT join_date FROM members ORDER BY join_date DESC LIMIT 1;"
    db, cursor = query_handle(query)
    first_data = cursor.fetchall()

    # 最前面不用加空格，最後面要加空格
    other_filter = ''

    if request.args.get('startdate'):
        start = request.args.get('startdate')
        end = request.args.get('enddate')
        ISOTIMEFORMAT = '%Y-%m-%d'
        start = dt.strptime(start,ISOTIMEFORMAT).replace(hour=00, minute=00)
        end = dt.strptime(end,ISOTIMEFORMAT).replace(hour=23, minute=59)

        if request.args.get('member_id'):
            member_id = request.args.get('member_id')
            other_filter = "{0} AND MID like '%{1}%' ".format(other_filter, member_id)
        if request.args.get('register'):
            register_index = request.args.get('register')
            register = ''
            if register_index == '1':
                register = 'First party'
            elif register_index == '2':
                register = 'LINE'
            elif register_index == '3':
                register = '臉書'
            other_filter = "{0} AND register like '%{1}%' ".format(other_filter, register)

        query_total = "SELECT * FROM members WHERE (STR_TO_DATE(join_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') {2} ORDER BY join_date DESC;" .format(start, end, other_filter)
        query_pag = "SELECT * FROM members WHERE (STR_TO_DATE(join_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') {2} ORDER BY join_date DESC LIMIT {3} OFFSET {4} ;" .format(start, end, other_filter, per_page, offset)

    else:
        query_total =  "SELECT * FROM members;"
        query_pag = "SELECT * FROM members ORDER BY join_date DESC LIMIT %s OFFSET %s ;" %(per_page, offset)

    # Executing a query to get the total number of members
    db, cursor = query_handle(query_total)
    global total
    total = cursor.fetchall()

    # Executing a query with LIMIT and OFFSET provided by the variables above
    db, cursor = query_handle(query_pag)
    members = cursor.fetchall()

    # Closing cursor
    cursor.close()

    # Setting up the pagination variable
    pagination = Pagination(page=page, per_page=per_page, offset=offset, total=len(total), record_name='members', css_framework='bootstrap3')

    db.close()
    if first_data:
        update = request.args.get('update') or  first_data[0][0] 
    else:
        update='No data'
    return render_template('member.html', members=members, pagination=pagination, newest_date=update)

def member_report():
    df = pd.DataFrame(total, columns=['會員ID', '會員群組', '標籤', '姓名', '電子郵件', '性別', '電話', 'Line ID', '生日', '加入日期', 'id', '臉書帳號', '註冊方式'])
    df.drop(['id'], axis=1, inplace=True)
    df.to_csv('filter_member.csv')
    return redirect(url_for('member_report_download'))

def member_report_download():
    return send_file("filter_member.csv",as_attachment=True, cache_timeout=0)

def clean_members():
    query = "truncate table members;"
    db, cursor = query_handle(query)
    db.commit()
    db.close()

def clean_specific_members():
    query = "Delete FROM members WHERE join_date > '2020-12-31';"
    db, cursor = query_handle(query)
    db.commit()
    db.close()

def member_crawler():
    # clean_members()
    # clean_specific_members()
    ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'
    now = datetime.datetime.now().strftime(ISOTIMEFORMAT)

    # 每天凌晨一點更新前一天的數據
    timer = threading.Timer(86400, member_crawler)
    timer.start()

    cap = DesiredCapabilities().CHROME
    cap["marionette"] = False
    browser =  webdriver.Remote(
                command_executor = CHROMEDRIVER_ADDRESS,
                desired_capabilities = cap)
    browser.maximize_window()  # 最大化視窗
    wait = WebDriverWait(browser, 10) # 等待載入10s


    LOGIN_URL = LOGIN_URL
    #get token
    res = requests.get(LOGIN_URL).text
    html = BeautifulSoup(res,"html.parser")
    token = html.find_all(type="hidden")[1]["value"]

    URL = MEMBER_URL+'&token='+token+'&page=1'

    browser.get(URL)
    browser.execute_script("document.getElementById('username').value='ACCOUNT'")
    browser.execute_script("document.getElementById('password').value='PASSWORD'")
    browser.execute_script("document.getElementById('btn-login').click()")
    time.sleep(5)
    df = pd.DataFrame()

    query =  "SELECT MID FROM members ORDER BY join_date DESC LIMIT 1;"
    db, cursor = query_handle(query)
    first_data = cursor.fetchall()

    while True: #全部頁數
        time.sleep(2) #載入會員列表
        soup = BeautifulSoup(browser.page_source,"html.parser")
        regex = re.compile('.*會員編號.*')
        member_list = soup.find_all("a",attrs = {"aria-label":regex})
        c_url = urlparse.urlparse(browser.current_url)
        print ("page {} start".format(parse_qs(c_url.query)['page'][0]))
        print(browser.current_url)
        for ti,member in enumerate(member_list): #1頁40筆
            if first_data[0][0] == member.attrs["aria-label"][5:]:
                break
            print(ti,member.attrs["aria-label"])
            for i in range(20):
                if i >= 19 :               
                    print("id timeout")  # 嘗試超過20次 print timeout
                    break
                try:
                    id = browser.find_element_by_xpath("//a[@aria-label='"+ member.attrs['aria-label'] + "']")
                    if id:
                        for i in range(20):
                            if i >= 19 :               
                                print("click member id timeout")  # 嘗試超過19次 print timeout
                                raise Exception
                            try:
                                browser.execute_script("arguments[0].scrollIntoView();", id)
                                id.click()
                                #避免沒有click進update頁面中
                                if 'update' in browser.current_url:
                                    break
                                else:
                                    raise Exception
                            except:
                                print('click member id again')
                                time.sleep(2)
                        break
                    else:
                        raise Exception
                except:
                    print('try member id again')
                    time.sleep(2)
            
            # tidy
            col_arr = []
            val_arr = []
            # cid
            col_arr.append('會員 ID')
            val_arr.append(member.attrs["aria-label"][5:])
            # customer_block
            content = BeautifulSoup(browser.page_source,"html.parser")
            customer_block = content.find("div",attrs = {"id":"tab-customer"})
            # title + value
            try:
                customer_block_info = customer_block.find_all('td')
            except:
                for i in range(20):
                    if i >= 19 :               
                        print("customer block timeout")  # 嘗試超過20次 print timeout
                        break
                    try:
                        content = BeautifulSoup(browser.page_source,"html.parser")
                        customer_block = content.find("div",attrs = {"id":"tab-customer"})
                        customer_block_info = customer_block.find_all('td')
                        break
                    except:
                        print('try customer block again')
                        time.sleep(2)
                # 預防增加會員時導致的id因為換頁而讀不到的問題
                if customer_block:
                    pass
                else:
                    c_url = browser.current_url
                    if 'update' in c_url:
                        browser.back() #若是停留在update介面要再回前一頁
                        continue #繼續下一筆
                    else:
                        print(c_url)
                        print("not in update page")
                        break
            
            pic_detect = False
            col_arr.append('註冊方式')
            if customer_block_info[0].find("small"):
                pic_detect = True
                val_arr.append(customer_block_info[0].find("small").get_text()[1:-3]) #註冊方式值
            else:
                val_arr.append("First party") #註冊方式值

            for ix,val in enumerate(customer_block_info):
                if pic_detect:
                    i = ix
                    if i == 0:
                        continue #有照片就省略下列步驟，整理下一組td
                else:
                    i = ix + 1
                if (i>18 and i<29) or i==31 or i==32:
                    continue #有些欄位不用紀錄，省略下列步驟，整理下一組td
                else:
                    if i%2==1: #column
                        if i ==3 or i==5 or i==7 or i==9 or i==11 or i==17:
                            col_arr.append(val.get_text()[2:])
                        else:
                            col_arr.append(val.get_text())
                    else: #value
                        if i==2: #會員群組值
                            val_arr.append(val.find('select', {'name':'customer_group_id'}).find('option', {'selected':'selected'})['value'])
                        elif i==4: #標籤值
                            val_arr.append(val.find("input",{'id': 'customer_label_cats_autocomplete'}).get('value'))
                        elif i==10: #性別值
                            val_arr.append(val.find('input',checked=True).get('value'))
                        elif i==30: #加入日期值
                            val_arr.append(val.get_text())
                        else: #其他input值
                            val_arr.append(val.find('input').get('value'))

            # put member in db
            query = 'INSERT INTO members(MID, register, member_group, tag, firstname, email, sex, phone, line_id, birthday, fb_account, join_date) VALUES("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}");'.format(val_arr[0],val_arr[1],val_arr[2],val_arr[3],escape(str(val_arr[4])),val_arr[5],val_arr[6],val_arr[7],escape(str(val_arr[8])),val_arr[9],escape(str(val_arr[10])),val_arr[11])
            db, cursor = query_handle(query)
            db.commit()
            db.close()
            # 前往下一個訂單編號
            browser.back()

        try:
            if first_data[0][0] == member.attrs["aria-label"][5:]:
                raise Exception
            c_url = urlparse.urlparse(browser.current_url)
            now_page = parse_qs(c_url.query)['page'][0]
            print ("page {} end".format(now_page))
            for i in range(20):
                if i >= 19 :               
                    print("next page timeout")  # 嘗試超過19次 print timeout
                    raise Exception
                try:
                    next = browser.find_element_by_xpath("//div[@class='links']/a[contains(text(), '›')]")
                    if next:
                        for i in range(20):
                            if i >= 19 :               
                                print("click next page timeout")  # 嘗試超過19次 print timeout
                                raise Exception
                            try:
                                next.click()
                                #避免沒有點進下一頁
                                c_url = urlparse.urlparse(browser.current_url)
                                if "update" in browser.current_url:
                                    print("in update")
                                    print (browser.current_url)
                                    browser.back()
                                    raise Exception
                                elif int(parse_qs(c_url.query)['page'][0]) == (int(now_page)+1):
                                    break #有點到下一頁
                                else:
                                    raise Exception
                            except:
                                print('click next again')
                                browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                                time.sleep(2)       
                        break
                    else:
                        raise Exception
                except:
                    print('try next again')
                    browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
        except:
            print('finish!')
            # 刪掉處理過久的重複值
            query = 'DELETE FROM members WHERE MID IN (SELECT MID FROM (select MID from members group by MID having count(*)>1) e) AND id NOT IN (SELECT id FROM (SELECT MIN(id) AS id from members group by MID having count(*)>1) t);'
            db, cursor = query_handle(query)
            db.commit()
            db.close()
            return redirect(url_for('member_page', update=now))
            break

# 設定 schedule 及執行
# 獲取現在時間
sched_now_time = datetime.datetime.now()
# 獲取明天時間
sched_next_time = sched_now_time + datetime.timedelta(days=+1)
sched_next_year = sched_next_time.date().year
sched_next_month = sched_next_time.date().month
sched_next_day = sched_next_time.date().day
# 獲取明天1點時間
sched_next_time = datetime.datetime.strptime(str(sched_next_year)+"-"+str(sched_next_month)+"-"+str(sched_next_day)+" 01:00:00", "%Y-%m-%d %H:%M:%S")

# 獲取距離明天1點時間，單位為秒
timer_start_time = (sched_next_time - sched_now_time).total_seconds()

# 定時器,參數為(多少時間後執行，單位為秒，執行的方法)
timer = threading.Timer(timer_start_time, member_crawler)
print("Member Timer go")
timer.start()