import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 1. 페이지 설정 및 따뜻한 테마 적용
st.set_page_config(page_title="Gemma-3 챗봇", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #FDFCF0; color: #433E3F; }
    .block-container { padding-top: 2rem; max-width: 800px; }
    [data-testid="stChatMessage"] {
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    h1 { color: #8D7B68 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 My 챗봇")
st.caption("⚙️ Groq Llama-3.1을 이용한 초고속 채팅 서비스(By rang)")

# 2. 보안 설정 (st.secrets 사용)
# .streamlit/secrets.toml 파일에 api_key = "여러분의_키" 가 있어야 합니다.
try:
    llm_cfg = st.secrets["api_key"]
except:
    st.error("Secrets에 'api_key'가 설정되지 않았습니다.")
    st.stop()

# 3. 모델 초기화 (LangChain 사용)
llm = ChatGroq(
    model="llama-3.1-8b-instant", 
    groq_api_key=llm_cfg,
    temperature=0.1,
    max_tokens=500,
)

# 4. 대화 내역 초기화 (시스템 메시지 포함)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "당신은 든든한 군인 AI 강미랑입니다. 군대 말투(~지 말입니다, ~습니까?)를 사용하십시오."}
    ]

# 5. 기존 대화 내역 표시 (시스템 메시지 제외)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 6. 사용자 입력 및 응답 로직
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 유저 메시지 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 7. Groq 응답 생성 (Streaming 지원)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # LangChain 형식에 맞게 메시지 변환
        langchain_messages = []
        for m in st.session_state.messages:
            if m["role"] == "system":
                langchain_messages.append(SystemMessage(content=m["content"]))
            elif m["role"] == "user":
                langchain_messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                langchain_messages.append(AIMessage(content=m["content"]))

        # 실시간 스트리밍 호출
        try:
            for chunk in llm.stream(langchain_messages):
                full_response += chunk.content
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            # 결과 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"에러가 발생했습니다: {e}")