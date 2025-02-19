import mysql.connector

# MySQL 연결 설정
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="0311"  # MySQL 비밀번호 입력
)

cursor = conn.cursor()

# 데이터베이스 생성
cursor.execute("CREATE DATABASE IF NOT EXISTS sparta_db")
print("Database 'sparta_db' created successfully")

# 연결 종료
cursor.close()
conn.close()
