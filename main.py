# 오른쪽 메인 영역에 버튼 클릭에 따른 메시지 출력
bun1 = """Visual Studio Code에서 파이썬 가상 환경을 설정하는 방법을 단계별로 쉽고 명확하게 안내할게요.



### 1단계: Python 및 가상 환경 모듈 설치 확인
- Python이 설치되어 있어야 하며, 기본적으로 `venv` 모듈이 포함되어 있습니다.
- 터미널에 `python --version` 또는 `python3 --version` 입력해 설치 확인하세요.

### 2단계: 프로젝트 폴더 열기
- Visual Studio Code에서 작업할 프로젝트 폴더를 엽니다.
- 메뉴 `파일 > 폴더 열기`로 이동하거나 폴더를 드래그해 띄우세요.

### 3단계: 가상 "환경 생성
- VSCode 내 터미널(단축키 `Ctrl + ~`)을 엽니다.
- 다음 명령어를 입력하여 가상 환경을 생성합니다.

```bash
python -m venv .venv
```

- `.venv`는 가상 환경 폴더 이름이며, 원하는 이름으로 바꿀 수 있습니다.

### 4단계: 가상 환경 활성화
- OS별 명령어로 활성화합니다.

| 운영체제 | 명령어                              |
|---|-----------------------------------|
| Windows  | `.venv\Scripts\activate`             |
| macOS/Linux | `source .venv/bin/activate`          |

- 활성화되면 터미널 앞에 환경 이름이 표시됩니다.

### 5단계: VSCode에서 인터프리터 설정
- 좌측 하단 또는 `Ctrl+Shift+P` → "Python: 인터프리터 선택" 검색 후 클릭
- 목록에서 생성한 `.venv` 폴더의 Python 인터프리터를 선택하세요.

### 6단계: 가상 환경 사용 준비 완료
- 이제 필요한 패키지 설치는 `pip install 패키지명` 명령으로 가상 환경에만 적용됩니다.
- 작업이 끝난 후 가상 환경 비활성화는 `deactivate` 명령으로 가능합니다.

---

이렇게 설정하면 프로젝트별로 독립된 환경을 구축해 패키지 충돌 걱정 없이 안정적으로 개발할 수 있어요. 도움이 필요하면 언제든 질문해 주세요. 화이팅!"
"""
ra1 = """ 1. visual studiocode 실행(가상환경 설정을 먼저하세요.) \n
          2. 새파일 main.py 생성 \n
          3. 제미나이 프롬프트 ~~
              -- stremlit을 이용해서 코딩하려고 하는데..
                 왼쪽에는 버튼하나, 라디오 버튼2개를 추가해줘.
                 버튼을 누르면 Hello를 
                라디오버튼1을 누르면 라디오버튼 1출력,
                라디오버튼2를 누르면 라디오버튼 2출력 해주는 코드를 작성해줘 \n
            4. 제미나이 답변
            Streamlit의 사이드바(Sidebar) 기능을 이용하면 왼쪽 영역에 위젯을 깔끔하게 배치할 수 있습니다. 요청하신 기능을 구현한 코드는 다음과 같습니다.
 \n
### Streamlit 위젯 배치 코드

```python
import streamlit as st

# 1. 사이드바 설정 (왼쪽 영역)
with st.sidebar:
    st.header("설정 메뉴")
    
    # 버튼 추가
    hello_btn = st.button("인사 버튼")
    
    # 라디오 버튼 추가
    # index=None을 설정하면 처음 실행 시 아무것도 선택되지 않은 상태로 만들 수 있습니다.
    radio_choice = st.radio(
        "원하는 옵션을 선택하세요",
        ["라디오버튼 1", "라디오버튼 2"],
        index=None
    )
 \n
# 2. 메인 화면 출력 로직
st.title("결과 화면")

# 버튼 클릭 시 출력
if hello_btn:
    st.write("### Hello")

# 라디오 버튼 선택 시 출력
if radio_choice == "라디오버튼 1":
    st.info("라디오버튼 1 출력")
elif radio_choice == "라디오버튼 2":
    st.success("라디오버튼 2 출력")

```

---
 \n
### 코드 설명

* **`st.sidebar`**: `with` 문과 함께 사용하면 그 안에 작성된 위젯들을 화면 왼쪽 사이드바에 고정시킵니다.
* **`st.button`**: 클릭하는 순간 `True`를 반환하여 `if` 문을 실행시킵니다.
* **`st.radio`**: 여러 옵션 중 하나를 선택할 수 있게 하며, 선택된 항목의 **텍스트 값**을 반환합니다.
* **`index=None`**: 앱이 처음 실행될 때 라디오 버튼이 미리 선택되어 있지 않도록 설정한 옵션입니다.

---
 \n
### 실행 방법

1. 위 코드를 `main.py`라는 이름으로 저장합니다.
2. 터미널(CMD)에서 해당 폴더로 이동한 뒤 아래 명령어를 입력합니다.
```bash
streamlit run main.py

```
 \n

3. (보기/터미널)  pip install streamlit
"""

        
import streamlit as st
st.header("🌸 3월14일 과제 점검 및 복습시간(By 미랑)")

@st.dialog("Visual Studio Code 가상환경 설정방법", width="large")
def show_venv_guide():
    st.write("### 💻 VS Code 가상환경 설정 순서")
    st.markdown(bun1)
    if st.button("닫기"):
        st.rerun()
# 사이드바 영역
with st.sidebar:
    options = ["3월 14일 과제 점검 및 복습시간~~~~", "오늘 과제 정답"]
    radio_option = st.radio("메시지 선택", options, index=0)
    
    # 버튼 클릭 시 다이얼로그 함수 호출
    if st.button("VS Code 가상환경 설정방법", type="primary"):
        show_venv_guide()

    selected_index = options.index(radio_option)

# 본문 영역
if selected_index == 0:
    st.write("~~Hello~~")
elif selected_index == 1:
    # ra1 변수가 정의되어 있어야 합니다.
    try:
        st.write(ra1)
    except NameError:
        st.error("오늘 과제 정답 데이터(ra1)가 정의되지 않았습니다.")

