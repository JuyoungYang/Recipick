import streamlit as st
import requests

# ===== DB 담당자가 구현할 부분 =====
# 1. Recipe 테이블 생성
#    - 레시피 이름 (recipe_name) : VARCHAR
#    - 조리시간 (cook_time) : VARCHAR
#    - 인분 수 (servings) : VARCHAR
#    - 재료 목록 (ingredients) : TEXT or JSON
#    - 조리 순서 (instructions) : TEXT or JSON
#    - 이미지 URL (image_url) : VARCHAR
# 2. 아래 데이터를 DB에 마이그레이션
# 3. 실제 서비스에 필요한 추가 데이터 입력

# UI 개발용 임시 데이터 (추후 DB 데이터로 교체)
RECIPE_DETAILS = {
    "김치볶음밥": {
        "cook_time": "15분",
        "servings": "2인분",
        "ingredients": [
            "밥 2공기",
            "김치 1컵",
            "햄 100g",
            "식용유 2큰술",
            "대파 1/2대",
            "참기름 1작은술",
        ],
        "instructions": [
            "재료를 준비합니다.",
            "팬을 달군 후 식용유를 둘러줍니다.",
            "김치를 넣고 볶아줍니다.",
            "밥을 넣고 골고루 섞어가며 볶아줍니다.",
            "마지막에 참기름을 둘러 향을 냅니다.",
        ],
    },
    "참치마요덮밥": {
        "cook_time": "5분",
        "servings": "1인분",
        "ingredients": [
            "밥 1공기",
            "참치캔 1개",
            "마요네즈 2큰술",
            "깨 약간",
            "파 조금",
            "간장 1작은술",
        ],
        "instructions": [
            "참치캔의 기름을 빼줍니다.",
            "참치와 마요네즈를 섞어줍니다.",
            "간장을 넣고 섞어줍니다.",
            "밥 위에 참치마요 무침을 올립니다.",
            "깨와 파를 뿌려 완성합니다.",
        ],
    },
    "베이컨김치볶음밥": {
        "cook_time": "20분",
        "servings": "2인분",
        "ingredients": [
            "밥 2공기",
            "김치 1컵",
            "베이컨 4장",
            "식용유 2큰술",
            "대파 1대",
            "계란 2개",
            "참기름 1작은술",
        ],
        "instructions": [
            "베이컨을 잘게 썰어줍니다.",
            "팬에 기름을 두르고 베이컨을 볶아줍니다.",
            "김치를 넣고 같이 볶아줍니다.",
            "밥을 넣고 골고루 섞어가며 볶아줍니다.",
            "계란프라이를 올리고 참기름을 둘러 완성합니다.",
        ],
    },
    "계란볶음밥": {
        "cook_time": "10분",
        "servings": "1인분",
        "ingredients": [
            "밥 1공기",
            "계란 2개",
            "대파 1/2대",
            "식용유 2큰술",
            "간장 1큰술",
            "소금 약간",
        ],
        "instructions": [
            "계란을 풀어서 준비합니다.",
            "팬에 기름을 두르고 계란을 살짝 스크램블합니다.",
            "밥을 넣고 계란과 함께 볶아줍니다.",
            "간장과 소금으로 간을 맞춥니다.",
            "대파를 넣고 살짝 더 볶아 완성합니다.",
        ],
    },
    "새우볶음밥": {
        "cook_time": "15분",
        "servings": "2인분",
        "ingredients": [
            "밥 2공기",
            "새우 200g",
            "당근 1/2개",
            "양파 1/2개",
            "계란 2개",
            "식용유 2큰술",
            "소금 약간",
        ],
        "instructions": [
            "새우는 껍질을 벗기고 다져줍니다.",
            "당근과 양파는 잘게 썰어줍니다.",
            "팬에 기름을 두르고 새우를 볶아줍니다.",
            "야채를 넣고 같이 볶다가 밥을 넣고 볶아줍니다.",
            "계란을 스크램블해서 넣고 소금으로 간을 맞춰 완성합니다.",
        ],
    },
}

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
    .st-emotion-cache-1v0mbdj {
        color: #7C523B;
    }
    .stMarkdown {
        color: #7C523B;
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

    # 조리시간 (다중 선택 가능 - 체크박스)
    st.markdown("### 조리시간")
    time_filters = {
        "5분 이내": st.checkbox("5분 이내", key="time_5min"),
        "5~15분": st.checkbox("5~15분", key="time_5_15min"),
        "15~30분": st.checkbox("15~30분", key="time_15_30min"),
        "30분 이상": st.checkbox("30분 이상", key="time_over_30min"),
    }

    # 선택된 조리시간 필터 저장
    selected_times = [time for time, selected in time_filters.items() if selected]

    # 양 (단일 선택 - 라디오 버튼)
    st.markdown("### 몇인분")
    serving_size = st.radio(
        "인분",
        options=["1인분", "2인분", "4인분", "6인분 이상"],
        key="serving_size",
        label_visibility="collapsed",
    )

    # 필터 초기화 버튼
    if st.button("필터 초기화"):
        # 세션 스테이트의 필터 관련 키들을 초기화
        for key in st.session_state.keys():
            if key.startswith("time_") or key == "serving_size":
                del st.session_state[key]

        # 체크박스와 라디오 버튼의 상태를 초기화
        st.session_state.time_5min = False
        st.session_state.time_5_15min = False
        st.session_state.time_15_30min = False
        st.session_state.time_over_30min = False
        st.session_state.serving_size = None  # 또는 "1인분"과 같은 기본값

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
        # 레시피 추천 목록이 있는 경우 버튼 표시
        if message["role"] == "assistant" and "recipes" in message:
            cols = st.columns(6)
            for i, recipe in enumerate(message["recipes"]):
                if cols[i].button(str(i + 1), key=f"recipe_{i}"):
                    st.session_state.selected_recipe = recipe
                    st.experimental_rerun()
            if cols[5].button("갱신", key="refresh"):
                st.experimental_rerun()

# ===== AI 담당자가 구현할 부분 =====
# 1. OpenAI API 연동
# 2. 사용자 입력 분석 로직
# 3. 레시피 추천 알고리즘 개발
# 4. 챗봇 응답 생성 로직
if query := st.chat_input(
    "예시: 볶음밥이 먹고싶어! 또는 김치로 만들 수 있는 요리 추천해줘!"
):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": query})

    # 임시 데이터 (AI 응답으로 대체 필요)
    recipes = [
        "김치볶음밥",
        "참치마요덮밥",
        "베이컨김치볶음밥",
        "계란볶음밥",
        "새우볶음밥",
    ]

    bot_response = """아래 목록중에 원하시는 레시피 번호를 클릭해주세요.
마음에 드는게 없다면 갱신을 눌러주세요."""

    # 봇 응답 저장 (레시피 목록 포함)
    st.session_state.messages.append(
        {"role": "assistant", "content": bot_response, "recipes": recipes}
    )

    st.experimental_rerun()

# ===== 백엔드 담당자가 구현할 부분 =====
# GET /api/recipes/{recipe_id} 엔드포인트 구현
# 레시피 상세 정보를 DB에서 조회하는 로직 구현
if st.session_state.selected_recipe:
    st.markdown("---")
    recipe = RECIPE_DETAILS[
        st.session_state.selected_recipe
    ]  # 이 부분을 API 호출로 대체

    # 제목
    st.title(st.session_state.selected_recipe)

    # 이미지 영역
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

    # 기본 정보
    st.header("🔸 기본 정보")
    st.write(f"• 조리시간: {recipe['cook_time']}")
    st.write(f"• 양: {recipe['servings']}")

    # 재료
    st.header("🔸 재료")
    for ingredient in recipe["ingredients"]:
        st.write(f"• {ingredient}")

    # 만드는 법
    st.header("🔸 만드는 법")
    for i, step in enumerate(recipe["instructions"], 1):
        st.write(f"{i}. {step}")

    # 뒤로가기 버튼
    if st.button("← 뒤로가기"):
        st.session_state.selected_recipe = None
        st.experimental_rerun()
