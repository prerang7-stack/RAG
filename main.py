import streamlit as st
import requests
import json

st.markdown("""
    <style>
    /* 1. 전체 배경 및 기본 폰트 설정 */
    .stApp {
        background-color: #FDFCF0; /* 아주 연한 크림색 */
        color: #433E3F; /* 따뜻한 느낌의 짙은 회색 */
    }

    /* 2. 중앙 컨텐츠 영역 설정 */
    .block-container {
        padding-top: 2rem;
        max-width: 800px; /* 가독성을 위해 너비 제한 */
    }

    /* 3. 챗봇 대화창(메시지) 스타일 살짝 조정 */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF; /* 메시지 배경은 깨끗한 화이트 */
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); /* 과하지 않은 그림자 */
        margin-bottom: 10px;
    }

    /* 4. 입력창 및 버튼 강조색 (인디안 핑크/베이지 계열) */
    .stChatInputContainer {
        padding-bottom: 2rem;
    }
    
    /* 버튼이나 강조 텍스트에 쓰일 따뜻한 색상 */
    h1, h2, h3, .st-emotion-cache-10trblm {
        color: #8D7B68 !important; /* 따뜻한 갈색 톤 */
    }

    /* 스크롤바 디자인 (선택사항) */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-thumb {
        background: #EADBC8;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 My 챗봇(By rang)")
st.caption("⚙️Ollama를 이용한 로컬 AI 채팅 서비스")

# 1. 대화 내역 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 든든한 군인 AI입니다. 군대 말투(~지 말입니다, ~습니까?)를 사용하십시오."}
    ]

for message in st.session_state.messages:
    if message["role"] != "system":  # 시스템 설정값은 화면에 출력 안 함
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
# 2. 기존 대화 내역 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. 사용자 입력 받기
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
  
    # 4. Ollama API 호출 (Gemma-3-1b-it-Q8_0)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Ollama 로컬 API 엔드포인트
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": "gemma-3-1b-it-Q8_0",
            "messages": st.session_state.messages,
            "stream": True  # 실시간 응답(Streaming) 활성화
        }

        try:
            response = requests.post(url, json=payload, stream=True)
            for i,line in enumerate(response.iter_lines()):
                if line:
                    chunk = json.loads(line)
                    # if i >10: break;
                    print(i,chunk)
                    
                    if "message" in chunk:
                        content = chunk["message"].get("content", "")
                        full_response += content
                        response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            # 어시스턴트 메시지 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except requests.exceptions.ConnectionError:
            st.error("Ollama가 실행 중인지 확인해주세요! (localhost:11434)")