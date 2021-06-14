from flask import render_template, flash, redirect, url_for, send_file
from db import query_handle
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def consumption_page():
    oneDayAgo = datetime.now() - timedelta(1)
    oneDayAgo = datetime.strftime(oneDayAgo, '%Y-%m-%d 23:59:59')
    oneYearAgo = datetime.now() - timedelta(1) - relativedelta(months=+11)
    oneYearAgo = datetime.strftime(oneYearAgo, '%Y-%m-01 00:00:00')

    query =  "SELECT quantity,sum,OID,user,purchase_date,MID FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') AND money_status='已付款' ORDER BY purchase_date DESC;".format(oneYearAgo, oneDayAgo)
    db, cursor = query_handle(query)
    orders = cursor.fetchall()

    query = "SELECT MID, user ,SUM(REPLACE(SUBSTRING(sum, 2),',','')) AS target, purchase_date FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') AND price!='$10' AND money_status='已付款' GROUP BY MID ORDER BY target DESC".format(oneYearAgo, oneDayAgo)
    db, cursor = query_handle(query)
    orders_rank1 = cursor.fetchall()

    query = "SELECT MID, user ,COUNT(DISTINCT OID) AS target, purchase_date FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') AND money_status='已付款' GROUP BY MID ORDER BY target DESC".format(oneYearAgo, oneDayAgo)
    db, cursor = query_handle(query)
    orders_rank2 = cursor.fetchall()

    # 排除海外運費專區跟贈品的數量
    query = "SELECT MID, user ,ROUND(SUM(quantity)/COUNT(DISTINCT OID),2) AS target, purchase_date FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') AND (price!='$0' OR price!='$10') AND money_status='已付款' GROUP BY MID ORDER BY target DESC".format(oneYearAgo, oneDayAgo)
    db, cursor = query_handle(query)
    orders_rank3 = cursor.fetchall()

    query = "SELECT MID, user ,ROUND(SUM(REPLACE(SUBSTRING(sum, 2),',',''))/COUNT(DISTINCT OID),2) AS target, purchase_date FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') AND price!='$10' AND money_status='已付款' GROUP BY MID ORDER BY target DESC".format(oneYearAgo, oneDayAgo)
    db, cursor = query_handle(query)
    orders_rank4 = cursor.fetchall()
    
    cursor.close()
    db.close()
    order_data = json.dumps([{"quantity": order[0], "sum": order[1], "OID": order[2], "user": order[3], "purchase_date": order[4], "MID": order[5]} for order in orders],ensure_ascii=False)
    order_rank1 = json.dumps([{"user": order[1], "target": order[2], "purchase_date": order[3]} for order in orders_rank1],ensure_ascii=False)
    order_rank2 = json.dumps([{"user": order[1], "target": order[2], "purchase_date": order[3]} for order in orders_rank2],ensure_ascii=False)
    order_rank3 = json.dumps([{"user": order[1], "target": order[2], "purchase_date": order[3]} for order in orders_rank3],ensure_ascii=False)
    order_rank4 = json.dumps([{"user": order[1], "target": order[2], "purchase_date": order[3]} for order in orders_rank4],ensure_ascii=False)
    return render_template("consumption.html", order_data = order_data, order_rank1 = order_rank1, order_rank2 = order_rank2, order_rank3 = order_rank3, order_rank4 = order_rank4)
    