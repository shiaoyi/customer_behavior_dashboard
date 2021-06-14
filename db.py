import pymysql

def query_handle(query):
    db = pymysql.connect(
        host='host',
        user='user',
        db='DBname',
        passwd='password',
        port=3306,
        charset="utf8"
    )
    cursor = db.cursor()
    cursor.execute(query)
    return db, cursor