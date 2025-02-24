import requests
import streamlit as st
BASE_URL = "http://localhost:8000"


# 레시피 정보를 API로부터 가져오는 함수
def get_recipe(recipe_id):
    try:
        response = requests.get(f"http://localhost:8000/api/recipes/{recipe_id}/")
        response.raise_for_status()
        return response.json()  # JSON 형태로 응답 반환
    except requests.exceptions.RequestException as e:
        st.error(f"레시피를 불러오는 데 실패했습니다: {str(e)}")
        return None  # 실패 시 None 반환


# 세션 상태 초기화 (메시지, 선택된 레시피 정보)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_recipe" not in st.session_state:
    st.session_state.selected_recipe = None

# 페이지 설정 (타이틀 및 레이아웃 설정)
st.set_page_config(
    page_title="Recipick", layout="wide", initial_sidebar_state="expanded"
)

# CSS 스타일 설정 (사이드바 색상 등)
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { background-color: #cfad99; }
    .st-emotion-cache-1v0mbdj { color: #7C523B; }
    .stMarkdown { color: #7C523B; }
    h1, h2, h3 { color: #7C523B; }
    /* 버튼 크기 통일 및 정렬 */
    .button-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
        align-items: flex-start;
    }
    .button-container button {
        width: 300px;
        text-align: left;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 8px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 사이드바 설정 (조리시간 필터, 인분 설정 등)
with st.sidebar:
    st.title("Recipick")
    time_filters = {
        "5분 이내": st.checkbox("5분 이내", key="time_5min"),
        "5~15분": st.checkbox("5~15분", key="time_5_15min"),
        "15~30분": st.checkbox("15~30분", key="time_15_30min"),
        "30분 이상": st.checkbox("30분 이상", key="time_over_30min"),
    }
    selected_times = [time for time, selected in time_filters.items() if selected]
    serving_size = st.radio(
        "인분",
        ["1인분", "2인분", "4인분", "6인분 이상"],
        key="serving_size",
        label_visibility="collapsed",
    )

    if st.button("필터 초기화"):
        for key in st.session_state.keys():
            if key.startswith("time_") or key == "serving_size":
                del st.session_state[key]
        st.session_state.time_5min = False
        st.session_state.time_5_15min = False
        st.session_state.time_15_30min = False
        st.session_state.time_over_30min = False
        st.session_state.serving_size = None
        st.experimental_rerun()

# 초기 메시지 표시 (대화창에 첫 메시지 띄우기)
if not st.session_state.messages:
    st.chat_message("assistant").write(
        "안녕하세요? 드시고 싶은 음식이나 사용하실 재료를 입력해주세요."
    )

# 이전 메시지 표시
for message_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])

        if (
            message["role"] == "assistant"
            and "recipes" in message
            and isinstance(message["recipes"], list)
        ):

            st.markdown('<div class="button-container">', unsafe_allow_html=True)

            # 레시피 버튼 생성
            for recipe_idx, recipe in enumerate(message["recipes"], 1):
                button_key = f"recipe_msg{message_idx}_recipe{recipe_idx}"
                # DB 컬럼명 CKG_NM 사용 (요리 이름)
                button_label = f"{recipe_idx}. {recipe.get('CKG_NM', '레시피')}"
                if st.button(button_label, key=button_key):
                    try:
                        recipe_response = requests.get(
                            f"http://localhost:8000/api/recipes/{recipe['id']}/"
                        )
                        recipe_response.raise_for_status()
                        recipe_detail = recipe_response.json()

                        # AI로 조리방법 생성 요청 → DB 컬럼 CKG_METHOD_CN 에 할당
                        instructions_response = requests.get(
                            f"http://localhost:8000/api/chatbot/generate-instructions/{recipe['id']}/"
                        )
                        if instructions_response.status_code == 200:
                            instructions_data = instructions_response.json()
                            recipe_detail["CKG_METHOD_CN"] = instructions_data.get(
                                "instructions", ""
                            )

                        # API 응답 구조에 따라 recipe 키가 존재할 수 있으므로 fallback 처리
                        st.session_state.selected_recipe = (
                            recipe_detail.get("recipe") or recipe_detail
                        )
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"레시피를 불러오는데 실패했습니다: {str(e)}")


            st.markdown("</div>", unsafe_allow_html=True)

# 선택된 레시피 세부 정보 표시
if st.session_state.selected_recipe:
    st.markdown("---")
    recipe = st.session_state.selected_recipe

    # DB 컬럼명 CKG_NM 사용 (요리 이름)
    title = recipe.get("CKG_NM") or "레시피"
    st.title(title)

    # DB 컬럼 RCP_IMG_URL 사용 (요리 이미지 URL)
    if recipe.get("RCP_IMG_URL"):
        st.image(recipe["RCP_IMG_URL"], width=400)

    st.header("🔸 기본 정보")
    # DB 컬럼 CKG_TIME_NM (조리 시간) 및 CKG_INBUN_NM (인분)
    st.write(f"• 조리시간: {recipe.get('CKG_TIME_NM', '-')}")
    st.write(f"• 인분: {recipe.get('CKG_INBUN_NM', '-')}")

    st.header("🔸 재료")
    # DB 컬럼 CKG_MTRL_CN 사용 (재료 목록)
    ingredients = recipe.get("CKG_MTRL_CN", "-")
    if isinstance(ingredients, str):
        for part in ingredients.split("|"):
            st.write(f"• {part.strip()}")
    else:
        st.write(ingredients)

    st.header("🔸 만드는 법")
    # DB 컬럼 CKG_METHOD_CN 사용 (조리 방법, AI 생성)
    instructions = recipe.get("CKG_METHOD_CN", "")
    if instructions:
        for i, step in enumerate(instructions.split("\n"), 1):
            if step.strip():
                st.write(f"{i}. {step.strip()}")
    else:
        st.write("조리 방법이 준비되지 않았습니다.")

    if st.button("← 뒤로가기"):
        st.session_state.selected_recipe = None
        st.experimental_rerun()


# 사용자 입력 받기
if query := st.chat_input(
    "예시: 볶음밥이 먹고싶어! 또는 김치로 만들 수 있는 요리 추천해줘!"
):
    st.session_state.messages.append({"role": "user", "content": query})

    if "session_id" not in st.session_state:
        st.session_state.session_id = "my-session-id"

    response = requests.post(
        "http://localhost:8000/api/chatbot/message/",
        json={"message": query, "session_id": st.session_state.session_id},
    )

    if response.status_code == 200:
        data = response.json()
        response_data = data.get("response", {})
        bot_text = response_data.get("response", "챗봇 응답을 받아오지 못했습니다.")
        recipes = response_data.get("recipes", [])

        st.session_state.messages.append(
            {"role": "assistant", "content": bot_text, "recipes": recipes}
        )

    st.rerun()

