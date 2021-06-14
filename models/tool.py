from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField, SelectField
from werkzeug.utils import secure_filename

from flask import render_template, flash, redirect, url_for, send_file, request
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename

from db import query_handle
import datetime

class showOrderForm(FlaskForm):
    upload = FileField('上傳訂單CSV檔案', validators=[FileRequired()])
    BRAND_CHOICES = [('D', 'D開頭品牌'), ('Z', 'Z開頭品牌'), ('C','C開頭品牌'), ('L','L開頭品牌')]
    brand = SelectField('品牌', choices=BRAND_CHOICES)
    submit = SubmitField('Submit')

def brand_filter(brand,file,filename):
    data = pd.read_csv(file)
    data = data.drop(['購買人','購買人電話','電子郵件','收件人','收件人電話','發票收件人','發票收件人電話'],axis=1)
    data['SKU'] = data['SKU'].astype('str')
    data['品牌'] = data['SKU'].map(lambda x : x[0])
    brandData = data[data['品牌']==brand]
    brandData = brandData.drop(['品牌'],axis=1)
    # 總計
    brandData.loc['總計','小計'] = brandData.loc[:,'小計'].sum()
    brandData.loc['總計'] = brandData.loc['總計'].fillna('')
    brandData.to_csv("brand_order.csv")

ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def filter():
    orderForm = showOrderForm()
    memberForm = showMemberForm()
    if orderForm.validate_on_submit():
        file = orderForm.upload.data
        brand = orderForm.brand.data
        if file.filename == '':
            flash('No selected file')
            return render_template('tool.html', orderForm=orderForm, memberForm=memberForm)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            brand_filter(brand,file,filename)
            flash('上傳成功')
            return redirect(url_for('download_file'))
        else:
            flash('檔案格式錯誤！請上傳 CSV 檔')
            return redirect(url_for('filter'))
    
    if memberForm.validate_on_submit():
        file = memberForm.upload.data
        if file.filename == '':
            flash('No selected file')
            return render_template('tool.html', orderForm=orderForm, memberForm=memberForm)
        if file and allowed_file(file.filename):
            lineid_data_filter(file)
            flash('上傳成功')
            return redirect(url_for('download_lineid_data'))
        else:
            flash('檔案格式錯誤！請上傳 CSV 檔')
            return redirect(url_for('filter'))
    return render_template('tool.html',orderForm=orderForm, memberForm=memberForm)

def download_file():
    return send_file("brand_order.csv",as_attachment=True, cache_timeout=0)

def user_record():
    orderForm = showOrderForm()
    memberForm = showMemberForm()
    usersData = []
    now = datetime.datetime.now()
    if request.args.get('user_ids'):
        ids = request.args.get('user_ids')
        # string to array and sort
        idsFilter = sorted(map(int,ids.strip().split()), reverse = True)
        # array合併成字串
        idsMember = ids.strip().replace(' ',',')
        memberQuery = "SELECT MID,sex,birthday,join_date FROM members WHERE MID IN({0}) ORDER BY CAST(MID as unsigned) DESC".format(idsMember)
        db, cursor = query_handle(memberQuery)
        memberData = cursor.fetchall()

        for i,id in enumerate(idsFilter):
            orderQuery = "SELECT OID,utm_source,product,quantity,sum,total,money_status,purchase_date FROM orders WHERE MID ='{0}'".format(id)
            db, cursor = query_handle(orderQuery)
            orderData = cursor.fetchall()
            if(len(orderData)==0):
                usersData.append(memberData[i])
            else:
                for j in range(len(orderData)):
                    userData = memberData[i] + orderData[j]
                    usersData.append(userData)
        usersDf = pd.DataFrame(usersData, columns=["會員ID","性別","年齡","加入日期","訂單ID","utm_source","產品","數量","總計","消費總金額","匯款狀態","購買日期"])
        usersDf['年齡'] = usersDf['年齡'].map(lambda x: now.year-int(x[:4]) if x[:4] != "0000" else 0)
        usersDf['性別'] = usersDf['性別'].map(lambda x: "女" if x=="1" else "男")
        usersDf.to_csv("users_data.csv")
        return redirect(url_for('download_user_record'))
    return render_template('tool.html', orderForm=orderForm, memberForm=memberForm)

def download_user_record():
    return send_file("users_data.csv",as_attachment=True, cache_timeout=0)

class showMemberForm(FlaskForm):
    upload = FileField('上傳會員CSV檔案', validators=[FileRequired()])
    submit = SubmitField('Submit')

def lineid_data_filter(file):
    lineidData = pd.read_csv(file)
    lineidData.drop(lineidData.columns[list(range(31))],axis=1,inplace=True)
    # 將累積次數的名字改成tag1,LINE_USERID的值改成userid
    lineidData.rename({'累積次數': 'tag1', 'LINE_USERID': 'userid'}, axis=1, inplace=True)
    # 刪除沒有 line user id 的值
    lineidData['userid'].replace('',np.nan,inplace=True)
    lineidData.dropna(subset=['userid'], inplace=True)
    # 購買次數的值轉成標籤
    lineidData['tag1'] = lineidData['tag1'].map(lambda x:'' if x==0 else '結帳頁拿回購金')
    #換位
    lineidData = lineidData[['userid','tag1']]
    lineidData.to_csv("lineid_import_data.csv", index=False)

def download_lineid_data():
    return send_file("lineid_import_data.csv",as_attachment=True, cache_timeout=0)