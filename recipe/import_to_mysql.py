import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

# MySQL 연결 설정
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "0311",     # 비밀번호 확인
    "database": "recipick",  # ✅ 데이터베이스 이름 확인
}

try:
    # CSV 파일 읽기 - 필요한 열만 선택
    df = pd.read_csv(
        "./data/recipe_01.csv",
        encoding="cp949",  # ✅ 인코딩 변경 (필요시 cp949 사용)
        usecols=["CKG_NM", "CKG_MTRL_CN", "CKG_INBUN_NM", "CKG_TIME_NM", "RCP_IMG_URL"]
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

except FileNotFoundError:
    print("❌ CSV 파일을 찾을 수 없습니다. 경로를 확인하세요.")
except mysql.connector.Error as db_err:
    print(f"❌ 데이터베이스 연결 오류: {db_err}")
except Exception as e:
    print(f"❌ 오류가 발생했습니다: {e}")