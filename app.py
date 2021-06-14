#!/usr/bin/env python
#coding=utf-8
from flask import Flask
from flask_bootstrap import Bootstrap
from config import Config
from models import tool,order,member,overview,consumption,profile,customer,repurchase,rfm

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config.from_object(Config)

app.add_url_rule('/', view_func=overview.overview_page, methods=['GET', 'POST'])

app.add_url_rule('/overview', view_func=overview.overview_page, methods=['GET', 'POST'])
app.add_url_rule('/profile', view_func=profile.profile_page, methods=['GET', 'POST'])
app.add_url_rule('/consumption', view_func=consumption.consumption_page, methods=['GET', 'POST'])
app.add_url_rule('/customer', view_func=customer.customer_page, methods=['GET', 'POST'])
app.add_url_rule('/repurchase', view_func=repurchase.repurchase_page, methods=['GET', 'POST'])
app.add_url_rule('/rfm', view_func=rfm.rfm_page, methods=['GET', 'POST'])

app.add_url_rule('/tool', view_func=tool.filter, methods=['GET', 'POST'])
app.add_url_rule('/tool/download', view_func=tool.download_file)
app.add_url_rule('/tool/user_record', view_func=tool.user_record, methods=['GET', 'POST'])
app.add_url_rule('/tool/user_record_download', view_func=tool.download_user_record)
app.add_url_rule('/tool/lineid_data', view_func=tool.lineid_data_filter, methods=['GET', 'POST'])
app.add_url_rule('/tool/lineid_data_download', view_func=tool.download_lineid_data)

app.add_url_rule('/order', view_func=order.order_page, methods=['GET', 'POST'])
app.add_url_rule('/order/page/<int:page>', view_func=order.order_page, methods=['GET', 'POST'])
app.add_url_rule('/order/crawler', view_func=order.order_crawler, methods=['GET'])
app.add_url_rule('/order/report', view_func=order.report)
app.add_url_rule('/order/report_download', view_func=order.report_download)

app.add_url_rule('/member', view_func=member.member_page, methods=['GET', 'POST'])
app.add_url_rule('/member/page/<int:page>', view_func=member.member_page, methods=['GET', 'POST'])
app.add_url_rule('/member/crawler', view_func=member.member_crawler, methods=['GET'])
app.add_url_rule('/member/report', view_func=member.member_report)
app.add_url_rule('/member/report_download', view_func=member.member_report_download)


if __name__=="__main__":
    app.run(debug=True, host='0.0.0.0', port=3000, use_reloader=False)