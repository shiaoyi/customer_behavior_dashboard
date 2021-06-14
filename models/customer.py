from flask import render_template, flash, redirect, url_for, send_file, request
from db import query_handle
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def customer_page():

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

        
    query =  "SELECT o1.MID,SUM(REPLACE(SUBSTRING(o1.sum, 2),',','')),o1.purchase_date,o1.OID,o2.OIDQ FROM orders AS o1 JOIN (SELECT MID, COUNT(DISTINCT OID) AS OIDQ FROM orders WHERE money_status='已付款' AND (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') < '{0}') GROUP BY MID HAVING OIDQ>1) AS o2 ON o1.MID = o2.MID WHERE price!='$0' GROUP BY o1.OID ORDER BY o1.MID DESC".format(endDate)
    db, cursor = query_handle(query)
    orders_all_old = cursor.fetchall()

    query = "SELECT old2.MID,SUM(REPLACE(SUBSTRING(old2.sum, 2),',','')),old2.purchase_date,old2.OID FROM (SELECT MID FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') < '{0}'))  AS old1 JOIN (SELECT MID,sum,purchase_date,OID FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{1}' AND '{2}') AND money_status='已付款') AS old2 ON old1.MID = old2.MID GROUP BY OID ORDER BY MID DESC".format(startDate, startDate, endDate)
    db, cursor = query_handle(query)
    orders_old = cursor.fetchall()

    query = "SELECT old2.MID,SUM(REPLACE(SUBSTRING(old2.sum, 2),',','')),old2.purchase_date,old2.OID FROM (SELECT MID FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') < '{0}'))  AS old1 RIGHT OUTER JOIN (SELECT MID,sum,purchase_date,OID FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{1}' AND '{2}') AND money_status='已付款') AS old2 ON old1.MID = old2.MID WHERE old1.MID IS null GROUP BY OID ORDER BY MID DESC".format(startDate, startDate, endDate)
    db, cursor = query_handle(query)
    orders_new = cursor.fetchall()

    
    
    cursor.close()
    db.close()
    order_all_oldcus = json.dumps([{"MID":order[0],"total":order[1],"purchase_date":order[2],"OID":order[3],"OIDQ":order[4]}for order in orders_all_old],ensure_ascii=False)
    order_oldcus = json.dumps([{"MID":order[0],"total":order[1],"purchase_date":order[2],"OID":order[3]}for order in orders_old],ensure_ascii=False)
    order_newcus = json.dumps([{"MID":order[0],"total":order[1],"purchase_date":order[2],"OID":order[3]}for order in orders_new],ensure_ascii=False)
    return render_template("customer.html",order_all_oldcus = order_all_oldcus, order_oldcus = order_oldcus, order_newcus = order_newcus, startDate=startDate, endDate=endDate)
    