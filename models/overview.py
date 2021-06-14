from flask import render_template, flash, redirect, url_for, send_file
from db import query_handle
import json
from datetime import datetime, timedelta

def overview_page():
    oneDayAgo = datetime.now() - timedelta(1)
    oneDayAgo = datetime.strftime(oneDayAgo, '%Y-%m-%d 23:59:59')
    twoDayAgo = datetime.now() - timedelta(2)
    twoDayAgo = datetime.strftime(twoDayAgo, '%Y-%m-%d 00:00:00')
    fifteenDayAgo = datetime.now() - timedelta(15)
    fifteenDayAgo = datetime.strftime(fifteenDayAgo, '%Y-%m-%d 00:00:00')

    query =  "SELECT * FROM members WHERE (STR_TO_DATE(join_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') ORDER BY join_date DESC;".format(twoDayAgo, oneDayAgo)
    db, cursor = query_handle(query)
    members = cursor.fetchall()

    query =  "SELECT * FROM orders WHERE (STR_TO_DATE(purchase_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') ORDER BY purchase_date DESC;".format(twoDayAgo, oneDayAgo)
    db, cursor = query_handle(query)
    orders = cursor.fetchall()

    query =  "SELECT register,join_date FROM members WHERE (STR_TO_DATE(join_date, '%Y-%m-%d %H:%i') BETWEEN '{0}' AND '{1}') ORDER BY join_date DESC;".format(fifteenDayAgo, oneDayAgo)
    db, cursor = query_handle(query)
    date_members = cursor.fetchall()
    
    cursor.close()
    db.close()
    order_data = json.dumps([{"sum": order[4], "OID": order[6], "purchase_date": order[20], "MID": order[26]} for order in orders],ensure_ascii=False)
    member_data = json.dumps([{"MID": member[0], "member_group": member[1], "tag": member[2], "firstname": member[3], "email": member[4], "sex": member[5], "phone": member[6], "line-id": member[7], "birthday": member[8], "join_date": member[9]} for member in members],ensure_ascii=False)
    date_member_data = json.dumps([{"register": member[0], "join_date": member[1]} for member in date_members],ensure_ascii=False)
    return render_template("overview.html",member_data = member_data, order_data = order_data, date_member_data = date_member_data)
    