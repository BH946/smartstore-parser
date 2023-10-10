import cgi
from src.db.db_proc import db # db 접속 함수

#############################################################

# 인증번호 쿼리 insert

form=cgi.FieldStorage()
authNum=form.getvalue('num')

cur=db.cursor()
sql = f"insert into auth_num(agency, number) values('NAVER', '{authNum}')"
cur.execute(sql)
db.commit()
db.close()


######### 사용안하게됨!@@@@@@@@@@###########