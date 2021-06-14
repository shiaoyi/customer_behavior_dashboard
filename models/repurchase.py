from flask import render_template, flash, redirect, url_for, send_file
from db import query_handle
import json
from datetime import datetime, timedelta

def repurchase_page():
    query =  "SELECT o1.MID,SUM(REPLACE(SUBSTRING(o1.sum, 2),',','')),o1.purchase_date,o1.OID,o2.OIDQ,o1.user FROM orders AS o1 JOIN (SELECT MID, COUNT(DISTINCT OID) AS OIDQ FROM orders WHERE money_status='已付款' GROUP BY MID HAVING OIDQ>1) AS o2 ON o1.MID = o2.MID WHERE price!='$0' GROUP BY o1.OID ORDER BY o1.MID,o1.purchase_date DESC"
    db, cursor = query_handle(query)
    orders_all_old = cursor.fetchall()
    
    cursor.close()
    db.close()
    order_all_oldcus = json.dumps([{"MID":order[0],"total":order[1],"purchase_date":order[2],"OID":order[3],"OIDQ":order[4],"user":order[5]}for order in orders_all_old],ensure_ascii=False)
    return render_template("repurchase.html",order_all_oldcus = order_all_oldcus)
    