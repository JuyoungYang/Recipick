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
    </style>
""",
    unsafe_allow_html=True,
)

# 사이드바 설정 (조리시간 필터, 인분 설정 등)
with st.sidebar:
    st.title("Recipick")
    # 조리시간 필터 (체크박스로 다중 선택 가능)
    time_filters = {
        "5분 이내": st.checkbox("5분 이내", key="time_5min"),
        "5~15분": st.checkbox("5~15분", key="time_5_15min"),
        "15~30분": st.checkbox("15~30분", key="time_15_30min"),
        "30분 이상": st.checkbox("30분 이상", key="time_over_30min"),
    }
    # 선택된 조리시간 필터 저장
    selected_times = [time for time, selected in time_filters.items() if selected]
    # 인분 수 설정 (단일 선택 라디오 버튼)
    serving_size = st.radio(
        "인분",
        options=["1인분", "2인분", "4인분", "6인분 이상"],
        key="serving_size",
        label_visibility="collapsed",
    )

    # 필터 초기화 버튼 (세션 상태 초기화 후 새로고침)
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

# 이전에 저장된 메시지들을 화면에 표시
for message_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])
        # assistant 메시지에 레시피가 있을 경우에만 버튼 표시
        if (
            message["role"] == "assistant"
            and "recipes" in message
            and isinstance(message["recipes"], list)
        ):
            # 버튼들을 세로로 배치
            for recipe_idx, recipe in enumerate(message["recipes"]):
                button_key = f"recipe_msg{message_idx}_recipe{recipe_idx}"
                if st.button(f"📝 레시피 {recipe_idx + 1} 보기", key=button_key):
                    try:
                        # 먼저 레시피 정보 가져오기
                        recipe_response = requests.get(
                            f"http://localhost:8000/api/recipes/{recipe['id']}/"
                        )
                        if recipe_response.status_code == 200:
                            recipe_detail = recipe_response.json()

                            # AI로 조리방법 생성 요청
                            instructions_response = requests.get(
                                f"http://localhost:8000/api/chatbot/generate-instructions/{recipe['id']}/"
                            )
                            if instructions_response.status_code == 200:
                                instructions_data = instructions_response.json()
                                # 생성된 조리방법을 레시피 상세 정보에 추가
                                recipe_detail["instructions"] = instructions_data.get(
                                    "instructions", ""
                                )

                            st.session_state.selected_recipe = recipe_detail.get(
                                "recipe", {}
                            )
                            st.experimental_rerun()

                    except Exception as e:
                        st.error(f"레시피를 불러오는데 실패했습니다: {str(e)}")

# 선택된 레시피에 대한 세부 정보 표시
if st.session_state.selected_recipe:
    st.markdown("---")
    recipe = st.session_state.selected_recipe

    # name이 빈 문자열일 경우 "레시피"로 표시
    title = recipe.get("name") or "레시피"
    st.title(title)

    # 이미지 크기 조절 (width=400 으로 설정)
    if recipe.get("image"):
        st.image(
            recipe.get("image"), width=400
        )  # use_column_width=True 제거하고 width 지정

    st.header("🔸 기본 정보")
    st.write(f"• 조리시간: {recipe.get('cook_time', '-')}")
    st.write(f"• 양: {recipe.get('servings', '-')}")

    st.header("🔸 재료")
    ingredients = recipe.get("ingredients", "-")
    if isinstance(ingredients, str):
        ingredients_parts = ingredients.split("|")
        for part in ingredients_parts:
            st.write(f"• {part.strip()}")
    else:
        st.write(ingredients)

    st.header("🔸 만드는 법")
    instructions = recipe.get("instructions")
    if instructions:
        steps = instructions.split("\n")
        for i, step in enumerate(steps, 1):
            if step.strip():
                st.write(f"{i}. {step.strip()}")
    else:
        st.write("조리 방법이 준비되지 않았습니다.")

    if st.button("← 뒤로가기"):
        st.session_state.selected_recipe = None
        st.experimental_rerun()

# 사용자 입력 받기 (입력된 쿼리에 대해 레시피 추천)
# ------------------------------
# 6. 사용자 입력 처리: 챗봇 입력창
# ------------------------------
if query := st.chat_input("예시: 볶음밥이 먹고싶어! 또는 김치로 만들 수 있는 요리 추천해줘!"):
    # 사용자 입력 메시지를 세션에 저장
    st.session_state.messages.append({"role": "user", "content": query})
    
    # session_id가 없으면 생성 (이미 있으면 그대로 사용)
    if "session_id" not in st.session_state:
        st.session_state.session_id = "my-session-id"  # [수정됨: 예시 session_id 생성]
    
    # bot_text 초기화 (모든 실행 경로에서 정의되도록)
    bot_text = ""  # [수정됨: 초기값 설정]
    recipes = []   # [수정됨: 초기값 설정]
    
    try:
        # 챗봇 API 호출 (POST /api/chatbot/message/)
        response = requests.post(
            f"{BASE_URL}/api/chatbot/message/",
            json={"message": query, "session_id": st.session_state.session_id},
        )
        response.raise_for_status()
        data = response.json()
        response_data = data.get("response", {})
        # bot_text에는 챗봇의 응답 텍스트가 저장되어야 함
        bot_text = response_data.get("response", "챗봇 응답을 받아오지 못했습니다.")  # [수정됨: bot_text 정의]
        recipes = response_data.get("recipes", [])  # [수정됨: recipes 정의]
    except Exception as e:
        # 예외 발생 시에도 bot_text와 recipes를 정의합니다.
        bot_text = f"오류 발생: {str(e)}"  # [수정됨: bot_text 정의 in except]
        recipes = []  # [수정됨: recipes 초기화 in except]
    
    # 챗봇 응답과 함께 추천 목록을 세션에 저장 (키: "recipes" 사용)
    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_text,  # [수정됨: bot_text 사용]
        "recipes": recipes    # [수정됨: recipes 사용]
    })
    
    st.experimental_rerun()  


# 선택된 레시피에 대한 세부 정보 표시
if st.session_state.selected_recipe:
    st.markdown("---")
    recipe_id = st.session_state.selected_recipe["id"]
    recipe = get_recipe(recipe_id)  # 선택된 레시피의 상세 정보 가져오기

    if recipe:
        st.title(recipe["name"])  # 레시피 제목
        st.image(
            recipe["image"], caption=recipe["name"], use_column_width=True
        )  # 이미지 표시

        # 기본 정보 (조리시간, 양)
        st.header("🔸 기본 정보")
        st.write(f"• 조리시간: {recipe['cook_time']}")
        st.write(f"• 양: {recipe['servings']}")

        # 재료 목록 표시
        st.header("🔸 재료")
        for ingredient in recipe["ingredients"]:
            st.write(f"• {ingredient}")

        # 만드는 법 표시
        st.header("🔸 만드는 법")
        for i, step in enumerate(recipe["instructions"], 1):
            st.write(f"{i}. {step}")

        # 뒤로가기 버튼 (상태 초기화 후 새로고침)
        if st.button("← 뒤로가기"):
            st.session_state.selected_recipe = None
            st.experimental_rerun()
