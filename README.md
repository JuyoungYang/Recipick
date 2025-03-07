# 스파르타 AI 9기 - 미니 팀프로젝트

# 🍽️ Recipick - AI 기반 레시피 추천 서비스

## 📌 프로젝트 개요

**Recipick**은 사용자의 취향과 입력에 따라 맞춤형 레시피를 추천하고, 부족한 레시피 데이터는 AI를 통해 자동 생성하여 풍부한 레시피 정보를 제공합니다. Streamlit 기반의 직관적인 UI와 챗봇 인터페이스를 활용하여 사용자가 쉽게 레시피를 검색하고 추천받을 수 있도록 설계되었습니다.

---

## 💁🏻 팀 소개

![Group_4](https://github.com/user-attachments/assets/100e5944-1c0f-42b8-9e52-e56468f70ff4)


---

## 🚀 핵심 기능

### 🥗 레시피 조회 및 추천

- 자연어 입력(예: "볶음밥이 먹고 싶어", "김치로 만들 수 있는 요리 추천해줘")을 기반으로 레시피 추천
- 필터 기능을 이용해 조리 시간, 인분 수 등 조건에 맞는 레시피 제공
- 중복 방지 로직을 적용하여 최대 5개의 레시피 추천

### 🤖 AI 레시피 생성

- 추천할 레시피가 부족할 경우 AI가 새로운 레시피를 자동 생성
- 생성된 레시피는 DB에 저장 후 사용자에게 제공
- 기본 이미지(`static/images/default_recipe.jpg`) 활용

### 👩‍🍳 조리 방법 자동 완성

- 조리법이 없는 레시피의 경우 AI를 활용하여 자동 생성
- 사용자가 특정 레시피를 선택할 경우 실시간으로 조리법 보완

### 💻 Streamlit 기반 UI

- 직관적인 사이드바 필터 제공 (조리 시간, 인분 수 등 설정 가능)
- 사용자 친화적인 디자인 적용 (컬러 커스터마이징 및 직관적 레이아웃)
- 필터 초기화 기능 제공

### 💬 챗봇 인터페이스

- 자연어 입력을 통한 레시피 추천 기능 제공
- 대화형 챗봇 UI를 통해 사용자 경험 향상
- 사용자의 이전 대화 내용 저장 및 반영하여 연속적인 대화 가능

---

## 🔧 기술 스택

### 🖥️ **프론트엔드**

- **Streamlit** (Python 기반 대화형 UI 프레임워크)
- **HTML, CSS** (기본적인 UI 스타일링)

### 🏗 **백엔드**

- **Django REST Framework (DRF)** (RESTful API 구축)
- **MySQL** (데이터베이스)
- **OpenAI API** (레시피 및 조리법 자동 생성)

---

## 🔗 API 설계 및 연동

### ✅ 주요 API 엔드포인트

| 엔드포인트 | 설명 |
| --- | --- |
| `/api/recipes/` | 필터링된 레시피 목록 조회 |
| `/api/recipes/recommend/` | 사용자 입력 기반 레시피 추천 |
| `/api/recipes/generate/` | AI 기반 레시피 생성 |
| `/api/recipes/details/<id>/` | 특정 레시피 상세 정보 조회 |
| `/api/chatbot/` | 자연어 입력을 통한 레시피 추천 |

### 🛠️ 주요 구현 사항

- **RESTful API 설계**: Django DRF 기반으로 효율적인 API 구조 설계
- **비동기 처리**: `requests` 라이브러리를 활용한 비동기적 요청 처리
- **에러 핸들링**: 예외 발생 시 적절한 응답 메시지 반환 (예: `404 Not Found`, `500 Internal Server Error`)

---

## 🤖 AI 연동 (OpenAI API)

- **DB의 레시피 부족 시** OpenAI API를 활용하여 자동으로 레시피 생성
- **데이터 베이스의 요리제목과 재료를 보고** AI가 자동으로 조리 방법을 생성
- **OpenAI 응답 데이터 가공 및 저장**하여 레시피 정보의 일관성 유지

📌 **핵심 구현 사항**

- AI를 통한 **데이터 보완 로직** 구축
- API 호출 시 **성공/실패 시나리오 처리**
- OpenAI 응답 형식에 맞춘 데이터 파싱 및 변환

---

## 📊 필터링 시스템 구현 (Streamlit)

- **조리 시간**, **인분 수** 등에 따라 레시피를 필터링할 수 있는 **인터랙티브 UI** 제공
- **사이드바 필터**를 활용하여 손쉽게 조건 변경 가능
- 챗봇을 통한 필터링 입력도 가능

📌 **핵심 구현 사항**

- Streamlit의 **Session State** 활용하여 상태 관리
- 동적인 UI 업데이트 및 사용자 입력 처리

---

## 💾 데이터베이스 설계

- **MySQL**을 활용하여 레시피 데이터를 구조화
- 레시피 추천 시 **중복 방지 로직** 적용
- AI가 생성한 레시피를 자동으로 DB에 저장

📌 **핵심 구현 사항**

- **효율적인 쿼리 최적화** (필터링 적용)
- **데이터 무결성 보장** (중복 레시피 방지)
- **AI 생성 데이터와 기존 데이터 통합 관리**

---

## 💬 챗봇 인터페이스

- **자연어 입력을 통한 레시피 추천**
- 사용자의 질문을 파싱하여 적절한 레시피 추천
- **대화 이력 저장**을 통해 연속적인 대화 가능
- 로딩 메세지를 출력하여 사용자 친화적인 사용환경

📌 **핵심 구현 사항**

- 자연어 입력 분석 → 레시피 추천 로직 적용
- 세션 기반 대화 상태 관리
- 예외 케이스 처리 (예: 지원되지 않는 입력, API 오류 등)
- `st.spinner` 활용하여 로딩 메세지 출력

---

## 📈 데이터 흐름

1. **사용자 입력 → 챗봇 API 호출**
2. **DB 조회 → 조건 충족 레시피 추천**
3. **레시피 부족 시 AI 생성 → DB 저장**
4. **Streamlit UI에 추천 레시피 표시**
5. **사용자가 선택한 레시피의 조리법 자동 보완**

---

## 🚀 프로젝트 실행 방법

### 1️⃣ **환경 설정**

```bash
# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

# 필수 라이브러리 설치
pip install -r requirements.txt
```

### 2️⃣ **Django 서버 실행**

```bash
python manage.py runserver
```

### 3️⃣ **Streamlit 실행**

```bash
streamlit run app.py
```

---

## 🎨 와이어프레임

<img width="1546" alt="2" src="https://github.com/user-attachments/assets/b8191504-8b64-467b-b106-690db1ca4e80" />
<img width="1546" alt="3" src="https://github.com/user-attachments/assets/b5a02d26-4e1d-4d26-98c1-5951a82e07ed" />
<img width="1546" alt="4" src="https://github.com/user-attachments/assets/04e7e463-f58c-43e8-a7a4-fec65e93719c" />
<img width="1546" alt="6" src="https://github.com/user-attachments/assets/3c3307be-bb38-493a-a169-0d44bf87613b" />
![Uploading 7.png…]()
![Uploading 8.png…]()


---

## 🌐 서비스 아키텍쳐

![image](https://github.com/user-attachments/assets/aebe9659-9d13-435d-b168-455be5c3ce11)


---

## 🧬 ERD

![image 1](https://github.com/user-attachments/assets/a72f9870-eac8-4a0b-adf0-102a6927a007)


---

## 🧐 개발 회고

### **1. 재료 안내의 중복**

- **문제:**
    
    현재 재료 정보는 DB에서 직접 조회 후 출력하고 이후 AI가 인분 수에 맞게 재료량을 조정해서 다시 출력하기 때문에 사용자 입장에서는 재료 안내가 두 번 나오는 현상이 발생.
    
- **개선 아이디어:**
    - 초기부터 AI에 인분 수를 반영하여 재료를 조정 → 한 번에 가공된 데이터 출력.
    - DB에서 가져온 기본 재료를 AI에 전달해 조정된 정보만 사용자에게 제공.
    - 사용자는 조정된 재료만 확인하도록 하여 정보의 중복을 제거.

### **2. 레시피 추천 결과의 한계**

- **문제:**
    
    필터링된 조건에 맞는 레시피가 DB에 적게 존재할 경우, 추천 결과가 1개 이하로 출력될 수 있음. 사용자는 기대한 만큼의 추천을 받지 못함.
    
- **현재 로직:**
    - DB에서 필터링 → 값이 없을 때만 AI 호출
    - AI 호출 조건: DB에 레시피가 부족할 때만 동작
- **개선 아이디어:**
    - 필터링 조건을 AI에게 전달하여 AI가 직접 조건에 맞는 레시피를 생성하거나 기존 레시피를 보완하게 함.
    - DB에서 필터링된 레시피가 적더라도 AI가 보완하여 최소한의 추천 수량을 유지.

### **3. 필터링으로 인한 데이터 중복 저장**

- **문제:**
    - 필터링 조건의 경우의 수가 많아짐 (조리시간 4개 * 인분 수 4개 → 16가지 조합)
    - 필터링 결과를 DB에 저장하기 때문에, 동일한 레시피라도 여러 번 저장되는 현상 발생 → DB 용량 낭비 가능성.
- **개선 아이디어:**
    - 가변 데이터(인분 수, 조리시간 등)는 DB에 저장하지 않고 계산된 값을 프론트에서 가공하거나, 캐시 처리.
    - 레시피 본체만 DB에 저장 → 필터링 정보는 별도의 가공 레이어에서 처리.
    - 또는, Redis 같은 인메모리 캐시를 활용해 자주 사용되는 필터링 조합만 임시 저장.

---

SA문서 : [https://www.notion.so/SA-19faf76d38e280a696f6db160b30bbb8](https://www.notion.so/SA-19faf76d38e280a696f6db160b30bbb8?pvs=21)
