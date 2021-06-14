from flask import render_template, flash, redirect, url_for, send_file
from db import query_handle
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def profile_page():
    oneDayAgo = datetime.now() - timedelta(1)
    oneDayAgo = datetime.strftime(oneDayAgo, '%Y-%m-%d 23:59:59')
    oneYearAgo = datetime.now() - timedelta(1) - relativedelta(months=+11)
    oneYearAgo = datetime.strftime(oneYearAgo, '%Y-%m-01 00:00:00')

    query =  "SELECT OID,utm_source,purchase_date,contact_address,MID FROM orders WHERE (purchase_date BETWEEN '{0}' AND '{1}') AND money_status='已付款' ORDER BY purchase_date DESC;".format(oneYearAgo, oneDayAgo)
    db, cursor = query_handle(query)
    orders = cursor.fetchall()

    query =  "SELECT members.MID,members.tag,members.sex,members.birthday,members.join_date,o1.purchase_date FROM members JOIN (SELECT MID,purchase_date FROM orders WHERE (purchase_date BETWEEN '{0}' AND '{1}')) AS o1 ON members.MID=o1.MID;".format(oneYearAgo, oneDayAgo)
    db, cursor = query_handle(query)
    members = cursor.fetchall()
    
    cursor.close()
    db.close()
    order_data = json.dumps([{"OID": order[0], "utm_source": order[1],"purchase_date": order[2], "contact_address": ('' if '＝＝' in order[3][:3] else order[3][:3]), "MID": order[4]} for order in orders],ensure_ascii=False)
    member_data = json.dumps([{"MID": member[0], "tag": member[1], "sex": member[2], "birthday": member[3], "join_date": member[4], "purchase_date":member[5]} for member in members],ensure_ascii=False)
    return render_template("profile.html",member_data = member_data, order_data = order_data)
    