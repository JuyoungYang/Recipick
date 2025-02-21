import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

# MySQL 연결 설정
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "0311",
    "database": "recipe",
}

try:
    # CSV 파일 읽기 - 필요한 열만 선택
    df = pd.read_csv(
        "./data/recipe_01.csv",
        encoding="cp949",
        usecols=["CKG_NM", "CKG_MTRL_CN", "CKG_INBUN_NM", "CKG_TIME_NM", "RCP_IMG_URL"],
    )

    # 결측치 처리
    df = df.fillna("")  # NULL 값을 빈 문자열로 변경

    # SQLAlchemy engine 생성
    engine = create_engine(
        f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
    )

    # DataFrame을 MySQL에 삽입
    df.to_sql("recipes", engine, if_exists="append", index=False)

    print("데이터가 성공적으로 삽입되었습니다!")
    print(f"총 {len(df)}개의 레시피가 추가되었습니다.")

except Exception as e:
    print(f"오류가 발생했습니다: {e}")
