import streamlit as st
import requests
import json

# ===== DB 담당자가 구현할 부분 =====
# 데이터베이스에서 레시피를 가져오는 함수
def get_recipe_from_db(recipe_name):
    import mysql.connector
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="your_database"
    )
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM recipe WHERE recipe_name = %s", (recipe_name,))
    recipe = cursor.fetchone()
    cursor.close()
    db.close()
    return recipe

# ===== 프론트엔드 영역 시작 =====
# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_recipe" not in st.session_state:
    st.session_state.selected_recipe = None

# 페이지 설정
st.set_page_config(
    page_title="Recipick", layout="wide", initial_sidebar_state="expanded"
)

# 스타일 설정
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #cfad99;
    }
    h1, h2, h3 {
        color: #7C523B;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 사이드바
with st.sidebar:
    st.title("Recipick")

    # 조리시간 (다중 선택 가능 - 체크박스) [충돌 해결]
    st.markdown("### 조리시간")
    time_filters = {
        "5분 이내": st.checkbox("5분 이내", key="time_5min"),
        "5~15분": st.checkbox("5~15분", key="time_5_15min"),
        "15~30분": st.checkbox("15~30분", key="time_15_30min"),
        "30분 이상": st.checkbox("30분 이상", key="time_over_30min"),
    }

    selected_times = [time for time, selected in time_filters.items() if selected]

    # 인분 선택 (라디오 버튼) [충돌 해결]
    st.markdown("### 몇인분")
    serving_size = st.radio(
        "인분",
        options=["1인분", "2인분", "4인분", "6인분 이상"],
        key="serving_size",
        label_visibility="collapsed",
    )

    # 필터 초기화 버튼
    if st.button("필터 초기화"):
        for key in st.session_state.keys():
            if key.startswith("time_") or key == "serving_size":
                del st.session_state[key]
        st.experimental_rerun()

# 초기 메시지 표시
if not st.session_state.messages:
    st.chat_message("assistant").write(
        "안녕하세요? 드시고 싶은 음식이나 사용하실 재료를 입력해주세요."
    )

# 저장된 메시지들 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and "recipes" in message:
            cols = st.columns(6)
            for i, recipe in enumerate(message["recipes"]):
                if cols[i].button(str(i + 1), key=f"recipe_{i}"):
                    st.session_state.selected_recipe = recipe
                    st.experimental_rerun()
            if cols[5].button("갱신", key="refresh"):
                st.experimental_rerun()

# ===== AI 담당자가 구현할 부분 =====
import openai
openai.api_key = "your_openai_api_key"

def get_recipe_recommendation(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "당신은 요리 추천 챗봇입니다."},
            {"role": "user", "content": user_input}
        ]
    )
    return response["choices"][0]["message"]["content"]

if query := st.chat_input(
    "예시: 볶음밥이 먹고싶어! 또는 김치로 만들 수 있는 요리 추천해줘!"
):
    st.session_state.messages.append({"role": "user", "content": query})

    recipes = ["김치볶음밥", "참치마요덮밥", "베이컨김치볶음밥", "계란볶음밥", "새우볶음밥"]
    bot_response = """아래 목록중에 원하시는 레시피 번호를 클릭해주세요.
마음에 드는게 없다면 갱신을 눌러주세요."""

    st.session_state.messages.append(
        {"role": "assistant", "content": bot_response, "recipes": recipes}
    )

    st.experimental_rerun()

# ===== 백엔드 담당자가 구현할 부분 =====
if st.session_state.selected_recipe:
    st.markdown("---")
    recipe = get_recipe_from_db(st.session_state.selected_recipe)

    st.title(st.session_state.selected_recipe)

    # 이미지 영역 (디자인 개선)
    st.markdown(
        """
    <div style="background-color: white; 
                width: 300px;                    
                height: 200px; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                margin: 20px 0; 
                border-radius: 10px; 
                border: 1px solid #9f6544;">
        이미지
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.header("🔸 기본 정보")
    st.write(f"• 조리시간: {recipe['cook_time']}")
    st.write(f"• 양: {recipe['servings']}")

    st.header("🔸 재료")
    for ingredient in json.loads(recipe["ingredients"]):
        st.write(f"• {ingredient}")

    st.header("🔸 만드는 법")
    for i, step in enumerate(json.loads(recipe["instructions"]), 1):
        st.write(f"{i}. {step}")

    if st.button("← 뒤로가기"):
        st.session_state.selected_recipe = None
        st.experimental_rerun()
