import streamlit as st

# 왼쪽 사이드바에 버튼 두 개 생성
with st.sidebar:
    btn1 = st.button("버튼1")
    btn2 = st.button("버튼2")

# 오른쪽 메인 영역에 버튼 클릭에 따른 메시지 출력
if btn1:
    st.write("안녕하세요.")
elif btn2:
    st.write("학습하자")