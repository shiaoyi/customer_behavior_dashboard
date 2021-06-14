from flask import render_template, flash, redirect, url_for, send_file, request
from db import query_handle
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def rfm_page():

    if request.args.get('startdate'):
        start = request.args.get('startdate')
        end = request.args.get('enddate')
        ISOTIMEFORMAT = '%Y-%m-%d'
        startDate = datetime.strptime(start,ISOTIMEFORMAT).replace(hour=00, minute=00)
        endDate = datetime.strptime(end,ISOTIMEFORMAT).replace(hour=23, minute=59)
    else:
        # 前一天
        oneDayAgo = datetime.now() - timedelta(1)
        endDate = datetime.strftime(oneDayAgo, '%Y-%m-%d 23:59:59')
        
        # 近一年內
        oneYearAgo = datetime.now() - timedelta(1) - relativedelta(months=+12)
        startDate = datetime.strftime(oneYearAgo, '%Y-%m-%d 00:00:00')

    vs_orders = []
    if request.args.get('vs_startdate'):
        s = request.args.get('vs_startdate')
        e = request.args.get('vs_enddate')
        ISOTIMEFORMAT = '%Y-%m-%d'
        s = datetime.strptime(s,ISOTIMEFORMAT).replace(hour=00, minute=00)
        e = datetime.strptime(e,ISOTIMEFORMAT).replace(hour=23, minute=59)

        query =  "SELECT MID, COUNT(DISTINCT OID) AS OIDQ, SUM(REPLACE(SUBSTRING(sum, 2),',','')), MAX(purchase_date), user FROM orders WHERE (purchase_date between '{0}' and '{1}') AND money_status='已付款' GROUP BY MID;".format(s,e)
        db, cursor = query_handle(query)
        vs_orders = cursor.fetchall()


    query =  "SELECT MID, COUNT(DISTINCT OID) AS OIDQ, SUM(REPLACE(SUBSTRING(sum, 2),',','')), MAX(purchase_date), user FROM orders WHERE (purchase_date between '{0}' and '{1}') AND money_status='已付款' GROUP BY MID;".format(startDate, endDate)
    db, cursor = query_handle(query)
    orders = cursor.fetchall()

    cursor.close()
    db.close()
    order_data = json.dumps([{"MID": order[0], "OIDQ": order[1], "total": order[2], "purchase_date": order[3], "user": order[4]} for order in orders],ensure_ascii=False)
    if vs_orders:
        vs_order_data = json.dumps([{"MID": order[0], "OIDQ": order[1], "total": order[2], "purchase_date": order[3], "user": order[4]} for order in vs_orders],ensure_ascii=False)
    else:
        vs_order_data = []
    return render_template("rfm.html",order_data = order_data, vs_order_data = vs_order_data, startDate=startDate, endDate=endDate)
    