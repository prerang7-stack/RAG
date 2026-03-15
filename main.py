import streamlit as st

# ... (기존 설정 및 테마 코드 생략) ...

st.title("🤖 My 챗봇")

# 버튼을 나란히 배치하기 위해 컬럼 생성
col2, col1, col3 = st.columns(3)

with col1:
    # 1번 버튼: Ollama
    target_url_1 = "https://ut4myvz5skrcz3rxfew66j.streamlit.app/"
    st.markdown(f"""
        <a href="{target_url_1}" target="_blank" style="text-decoration: none;">
            <div style="
                width: 100%;
                padding: 0.7em 0;
                color: #FFFFFF;
                background-color: #FFB7C5;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            ">
                🏠 Ollama OFFLINE 앱 열기
            </div>
        </a>
        """, unsafe_allow_html=True)

with col2:
    # 2번 버튼: Groq
    target_url_2 = "https://vevqhvemnzawe3xbh3u93k.streamlit.app/"
    st.markdown(f"""
        <a href="{target_url_2}" target="_blank" style="text-decoration: none;">
            <div style="
                width: 100%;
                padding: 0.7em 0;
                color: #FFFFFF;
                background-color: #8D7B68;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            ">
                ⚡ Groq ONLINE 앱 열기
            </div>
        </a>
        """, unsafe_allow_html=True)

with col3:
    # 3번 버튼: 예시로 Gemini 또는 다른 앱 연결
    target_url_3 = "https://d2hgfy4znfqb4dssaeakyb.streamlit.app/" # 연결할 실제 주소로 변경하세요
    st.markdown(f"""
        <a href="{target_url_3}" target="_blank" style="text-decoration: none;">
            <div style="
                width: 100%;
                padding: 0.7em 0;
                color: #FFFFFF;
                background-color: #4A90E2; /* 파란색 계열 */
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            ">
                🌟 MY RAG
            </div>
        </a>
        """, unsafe_allow_html=True)
    
st.divider() 

# ... (이후 챗봇 메시지 로직) ...