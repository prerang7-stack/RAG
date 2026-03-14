#👧🏻🤖🧠🇦🇮👾⚙️🟢🔴😊✨💡💾🔥֎🧮👍📢🤩📢🤩🟥🟩🟫🟫🟧✈️😍🔬⏰⏱✈️😍🔬⏰⏱✔️☑️ ✔️ ✔❌☑♻️👩🏻‍💻📓✍🏻💡🦜📢🎙🎧🔊🎙️🎤✨💫🌛💜🏝️🍹⛱️🌞 🌊🎥☕☕💻 
import streamlit as st
import os
import pickle
import hashlib
import datetime
import json
from typing import List, Dict, Tuple #
import shutil
from collections import defaultdict
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever

# 3. 추가로 필요한 임포트들 (최신 버전 기준)
from numpy.ma.mrecords import addfield
import yaml
from datetime import datetime
import pytz  # 시간대 설정을 위해 필요 (pip install pytz)
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config
import re
import sqlite3
from collections import Counter

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

model_name = "intfloat/multilingual-e5-large"
encode_kwargs = {'normalize_embeddings': True}

EMBEDDING_MODEL = HuggingFaceEmbeddings(
    model_name=model_name,
    encode_kwargs=encode_kwargs
)

# --- 1. 설정 및 초기화 ---
# EMBEDDING_MODEL = "bge-reranker-v2-m3-q4_k_m"   #임베딩 모델. 동작 확인, BGE모델의 max chunk_size = 512 token임. 매우 중요
# LLM_MODEL = "gemma-3-27b-it.Q4_K_M"                          #LLM모델
# EMBEDDING_MODEL = "multilingual-e5-large-instruct-q8_0"   #임베딩 모델

# LLM_MODEL = ChatGroq(model="llama-3.1-8b-instant", api_key="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")
config = st.secrets 
llm_cfg = config['api_key']
llm = ChatGroq(
        # llama-3.1-8b 보다 더 최적화된 응답을 보여주는 모델
        model="llama-3.1-8b-instant", 
        groq_api_key=llm_cfg,
        temperature=0.1,
        # 속도를 극대화하기 위한 설정
        max_tokens=500, # 답변 길이를 더 짧게 제한
    )
                   #LLM모델
DB_PATH = "./faiss_db"                                    #벡터DB저장
UPLOAD_PATH = "./uploaded_files"                          #문서저장
UPLOADED_FILES_INFO_FILE = os.path.join(UPLOAD_PATH, "uploaded_files.json") #업로드파일 목록/해시저장
HISTORY = "./chat_history/"                                #사용자 질의 이전 내용 저장(40개)
CONFIG_FILE = 'config.yaml'
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
DEFAULT_K_VALUE = 7

#** DB 연결 ################################################################################################
def init_db():
    """데이터베이스 초기화 및 초기 관리자 계정 생성"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()    
    # 1. users 없을시 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            name TEXT,
            role TEXT,
            available TEXT DEFAULT 'N'
        )
    ''')    
    # 2. SystemAdmin 권한을 가진 사용자가 있는지 확인
    c.execute("SELECT COUNT(*) FROM users WHERE role = 'SystemAdmin'")
    admin_exists = c.fetchone()[0]    
    # 3. 만약 관리자가 없다면 초기 관리자(admin) 생성
    if admin_exists == 0:
        admin_username = 'admin'
        admin_password = '1'  # 초기 비밀번호
        admin_name = 'admin'
        admin_role = 'SystemAdmin'
        admin_available = 'Y'        
        # 비밀번호 SHA-256 해싱
        hashed_pw = hashlib.sha256(admin_password.encode()).hexdigest()        
        # INSERT 실행
        c.execute('''
            INSERT INTO users (username, password, name, role, available) 
            VALUES (?, ?, ?, ?, ?)
        ''', (admin_username, hashed_pw, admin_name, admin_role, admin_available))        
        print(f"📢 초기 관리자 계정이 생성되었습니다. (ID: {admin_username} / PW: {admin_password})")
    
    conn.commit()
    conn.close()

########################################################################################################
# 1. 환경 정리
########################################################################################################

#** DB Con
init_db()

#** 초기 디렉토리 생성
for path in [DB_PATH, UPLOAD_PATH, HISTORY]:
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"{path} 디렉토리를 생성 했습니다.")

st.set_page_config(page_title="TO", layout="wide")

#** 세션 상태 초기화
if "confirm_delete_db" not in st.session_state:
    st.session_state.confirm_delete_db = None

if "vectorstore" not in st.session_state:
    if os.path.exists(os.path.join(DB_PATH, "index.faiss")):
        embeddings = EMBEDDING_MODEL
        st.session_state.vectorstore = FAISS.load_local( DB_PATH, EMBEDDING_MODEL, allow_dangerous_deserialization=True)
        #--- DB 로드 싯점에 임베딩 테스트 출력 ---
        test_sentence = "안녕하세요"
        test_embedding = embeddings.embed_query(test_sentence)
        st.sidebar.success(f"임베딩 모델 테스트 성공:  임베딩 완료! (차원: {len(test_embedding)})")
        print(f"[DEBUG] 임베딩 모델 테스트: '{test_sentence}' -> 첫 5개 값: {test_embedding[:5]}")
    else:
        st.session_state.vectorstore = None

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

########################################################################################################
# 2. 함수들 정의
#########################################################################################################
    #####################################################################################################
    # 2.1. 사용자 관련 함수
    #####################################################################################################
#** 사용자 Insert
def add_user_to_db(username, password, name, role):
    """사용자를 DB에 추가합니다."""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        # 비밀번호 해싱
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        c.execute('INSERT INTO users (username, password, name, role, available) VALUES (?, ?, ?, ?, ?)',
                  (username, hashed_pw, name, role, 'N'))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # 중복 아이디 에러
    finally:
        conn.close()    

#** 사용자 존재하는지 확인해보기
def is_username_taken(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # 해당 아이디를 가진 행(row)이 있는지 조회
    c.execute('SELECT 1 FROM users WHERE username = ?', (username,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

#** 사용자 등록 화면
@st.dialog("️사용자 등록", width="large")
def show_userapplication_dialog():
    new_username = st.text_input("아이디 (Username)")
    new_password = st.text_input("비밀번호 (Password)", type="password")
    new_name = st.text_input("이름 (Full Name)")
    new_role = st.selectbox("권한 (Role)", ["User", "Manager"])

    if new_username and len(new_username) < 5:
        st.warning("⚠️ 아이디는 최소 5자리 이상이어야 합니다.")
        pw_valid = False
    else:
        pw_valid = True

        password_regex = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{9,}$"
        if new_password:
            if not re.match(password_regex, new_password)  and len(new_username) >= 9 :
                st.warning("⚠️ 비밀번호는 9자 이상이며, 영문, 숫자, 특수문자를 각각 최소 1개 이상 포함해야 합니다.")
                pw_valid = False
            else:
                st.success("✅ 안전한 비밀번호입니다.")
                pw_valid = True

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 저장하기", disabled=not pw_valid, use_container_width=True):
            if new_username and new_password and new_name:
                # 1단계: 중복 아이디 체크 (기존 any() 대신 사용)
                if is_username_taken(new_username):
                    st.error(f"이미 존재하는 아이디입니다: {new_username}")
                else:
                    # 2단계: 데이터 추가 (성공 시 True 반환)
                    success = add_user_to_db(new_username, hashlib.sha256(str.encode(new_password)).hexdigest(), new_name, new_role)
                    if success:
                        st.success(f"🎉 '{new_name}'님이 등록되었습니다. 관리자 승인을 기다려주세요.")
                        st.balloons()
                    else:
                        st.error("등록 중 오류가 발생했습니다.")
            else:
                st.warning("모든 정보를 입력해 주세요.")
    with col2:
        if st.button("❌ 닫기", use_container_width=True):
           st.rerun()

#** 관리자 모드(사용자 관리)
@st.dialog("관리자 사용자 관리 모드", width="large")
def admin_page():  
    conn = sqlite3.connect('users.db')
    df = pd.read_sql_query("SELECT username, name, role, available FROM users", conn)
    
    # 1. 표로 보여주기
    st.dataframe(df, use_container_width=True)
    
    # 2. 특정 유저 승인하기
    st.subheader("사용자 승인 및 삭제")
    target_user = st.selectbox("대상 사용자 선택", df['username'].tolist())
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 승인 (N -> Y)"):
            c = conn.cursor()
            c.execute("UPDATE users SET available = 'Y' WHERE username = ?", (target_user,))
            conn.commit()
            st.success(f"{target_user}님 승인 완료!")
            st.rerun()

    # 2. 특정 유저 삭제하기      
    with col2:
        if st.button("🗑️ 사용자 삭제"):
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE username = ?", (target_user,))
            conn.commit()
            st.warning(f"{target_user}님 삭제 완료!")
            st.rerun()
    conn.close()

    #####################################################################################################
    # 2.2. Document 관련 함수
    #####################################################################################################

#** 파일 내용의 SHA256 해시를 계산
def calculate_file_hash(file_content) -> str:
    hasher = hashlib.sha256()
    hasher.update(file_content)
    return hasher.hexdigest()

#** 등록된 파일의 레지스트리 (파일명:해시)를 로드
def load_uploaded_files_registry() -> Dict[str, str]:
    if os.path.exists(UPLOADED_FILES_INFO_FILE):
        with open(UPLOADED_FILES_INFO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

#**등록된 파일의 레지스트리 (파일명:해시)를 저장
def save_uploaded_files_registry(registry: Dict[str, str]):
    with open(UPLOADED_FILES_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4)

    #####################################################################################################
    # 2.3. USER 질의 이력 관리 함수
    #####################################################################################################
#** 유저별 질의 이력 저장
def save_chat_history():
    if len(st.session_state.chat_history) > 40:
        st.session_state.chat_history = st.session_state.chat_history[-40:]
    with open(HISTORY_PATH, "wb") as f:
        pickle.dump(st.session_state.chat_history, f)
        print(f"사용자 질의 이력이 저장 되었습니다. {HISTORY_PATH}")
        
    #####################################################################################################
    # 2.4. VectorStore 관련 함수
    #####################################################################################################
#** Document 메타 및 텍스트 분할하기
def process_pdf(file):
    file_path = os.path.join(UPLOAD_PATH, file.name)
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
        #print(f"{file_path} 에 저장해(백업) 두었습니다.")
    # pdf파일 로드
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    #print(f"documents 길이: {len(documents)}")
    #메타정보 추가하기 --> 기존 제공 메타정보도 있음
    for doc in documents:
        doc.metadata["source"] = file.name
        doc.metadata["file_size"] = file.size
    #청크만들기
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = text_splitter.split_documents(documents)
    return chunks

#** 기존 벡터DB에 추가
        # 기존 DB에서 해당 파일명이 포함된 인덱스 제거 후 업데이트하는 로직
        # FAISS는 부분 삭제가 복잡하므로, 메타데이터 필터링을 통해 새롭게 구성하거나 전체 재빌드 권장
        # 여기서는 기존 DB에 추가하는 방식을 취하며, 중복 관리는 파일 업로드 단계에서 제어
# def update_vectorstore(new_chunks, file_name):
#     embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
#     if st.session_state.vectorstore is not None:
#         st.session_state.vectorstore.add_documents(new_chunks)
#     else:
#         clean_chunks = [doc for doc in new_chunks if doc.page_content.strip()]
#         # clean_chunks = clean_chunks[:18]
#         # for i, doc in enumerate(clean_chunks):
#         #     print(f"\n\n############\n{i} : : {doc}")
#         st.session_state.vectorstore = FAISS.from_documents(clean_chunks, embeddings)
#     st.session_state.vectorstore.save_local(DB_PATH)

def update_vectorstore(new_chunks, file_name):
    # 전역 변수로 선언된 EMBEDDING_MODEL(HuggingFace)을 사용합니다.
    # 만약 함수 인자로 전달받지 않았다면 상단의 EMBEDDING_MODEL을 참조합니다.
    
    if st.session_state.vectorstore is not None:
        st.session_state.vectorstore.add_documents(new_chunks)
    else:
        # OllamaEmbeddings 대신 상단에서 선언한 HuggingFaceEmbeddings 객체 사용
        st.session_state.vectorstore = FAISS.from_documents(new_chunks, EMBEDDING_MODEL)
    
    # 로컬에 저장
    st.session_state.vectorstore.save_local(DB_PATH)

#** 벡터DB 완전 삭제
def reset_database():
    st.sidebar.info("DB 초기화를 시작합니다...")
    # FAISS DB 디렉토리 삭제
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
        st.sidebar.success(f"FAISS DB 디렉토리 '{DB_PATH}' 삭제 완료.")
    # 업로드된 파일 정보 JSON 파일 삭제 (registry)
    if os.path.exists(UPLOADED_FILES_INFO_FILE):
        os.remove(UPLOADED_FILES_INFO_FILE)
        st.sidebar.success(f"업로드 파일 레지스트리 '{UPLOADED_FILES_INFO_FILE}' 삭제 완료.")
    # 채팅 이력 Pickle 파일 삭제
    if os.path.exists(HISTORY_PATH):
        os.remove(HISTORY_PATH)
        st.sidebar.success(f"채팅 이력 '{HISTORY_PATH}' 삭제 완료.")
    # 업로드된 원본 파일 백업 디렉토리 비우기
    if os.path.exists(UPLOAD_PATH):
        for file_name in os.listdir(UPLOAD_PATH):
            file_path = os.path.join(UPLOAD_PATH, file_name)
            # .gitkeep 파일 등 예외 처리 (만약 있다면)
            # 'uploaded_files_registry.json' 파일 자체는 'uploaded_files_registry.json'에서 지워졌으니 여기서는 원본 파일만
            if os.path.isfile(file_path) and file_name != os.path.basename(UPLOADED_FILES_INFO_FILE):
                try:
                    os.remove(file_path)
                except Exception as e:
                    st.sidebar.warning(f"파일 삭제 오류: {file_path} - {e}")
        st.sidebar.success(f"업로드된 원본 파일 백업 디렉토리 '{UPLOAD_PATH}' 비우기 완료.")

    # Streamlit 세션 상태 초기화 (메모리 상의 데이터도 비움)
    st.session_state.vectorstore = None
    st.session_state.uploaded_files_registry = {}  # DB에 임베딩된 파일들의 메타 정보
    st.session_state.chat_history = []
    st.sidebar.success("DB 초기화 및 세션 상태 업데이트 완료. 잠시 후 새로고침 됩니다.")
    # 재로드를 위해 app 강제 재실행
    # st.rerun()

    #####################################################################################################
    # 2.5. 온톨로지 관련 함수
    #####################################################################################################
    #**텍스트에서 조사 및 불용어를 제거하고 의미 있는 핵심 단어 n개를 추출
def extract_keywords_from_text(text, exclude_word, top_n=2):
    
    # 1. 한글, 영문, 숫자만 남기고 나머지는 공백 처리 (특수문자 제거)
    clean_text = re.sub(r'[^가-힣A-Za-z0-9\s]', ' ', text)
    
    # 2. 한국어 조사 제거 패턴 (단어 끝에 붙는 조사들)
    # 은/는, 이/가, 을/를, 의, 에, 로/으로, 과/와, 도, 에서, 만, 까지, 부터, 에게, 보다 등
    josa_pattern = r'(은|는|이|가|을|를|의|에|로|으로|과|와|도|에서|만|까지|부터|에게|보다)$'
    
    # 공백 기준으로 단어 분리
    raw_words = clean_text.split()
    processed_words = []
    
    # 3. 불용어(Stopwords) 제거 리스트 확장
    stopwords = [
        '대한', '있는', '통해', '관련', '위해', '경우', '데이터', '추출', '따라', '하여야','한다','때에',
        '또는', '조의', '조에', '하여', '하고', '이며', '및', '즉', '등의', "따른","의하여"
    ]
    
    for word in raw_words:
        # 단어 끝의 조사 제거 (예: "결과가" -> "결과", "데이터의" -> "데이터")
        clean_word = re.sub(josa_pattern, '', word)
        
        # 4. 필터링 조건: 
        # - 2글자 이상 (1글자 조사/단어 제외)
        # - 검색어(exclude_word)와 일치하지 않음
        # - 불용어 리스트에 포함되지 않음
        if (len(clean_word) > 1 and 
            clean_word != exclude_word and 
            clean_word not in stopwords):
            processed_words.append(clean_word)
    
    # 5. 가장 많이 등장한 단어 순으로 상위 n개 반환
    most_common = Counter(processed_words).most_common(top_n)
    return [word for word, count in most_common]

def extract_ontology_relations(query_concept, top_k=5):
    if st.session_state.vectorstore is None:
        return "벡터 DB가 비어 있습니다."

    results = st.session_state.vectorstore.similarity_search_with_score(query_concept, k=top_k)

    ontology_list = []
    for doc, score in results:
        # 관계 정의 (유사도 기반)
        if score < 0.2:
            relation = "핵심 관련어"
        elif score < 0.4:
            relation = "연관 개념"
        else:
            relation = "잠재적 맥락"

        # 핵심 키워드 추출 (파일 이름 대신 실제 단어 추출)
        keywords = extract_keywords_from_text(doc.page_content, query_concept, top_n=2)

        for word in keywords:
            ontology_list.append({
                "Relation": relation,
                # "Source": query_concept,
                "Target": word,  # ← 여기가 단어로 바뀌었습니다!
                "Confidence": round(1 - score, 4) if score <= 1 else 0.01 ,
                "Excerpt": doc.page_content[:10] + "...",  # 관련 내용 요약       
            })

    # 중복된 Target 제거 (서로 다른 청크에서 같은 단어가 나올 수 있음)
    df = pd.DataFrame(ontology_list).drop_duplicates(subset=['Target'])
    return df

#** 그래프 보기
def display_knowledge_graph(concept, relation_df):
    nodes = []
    edges = []
    
    nodes.append(Node(
        id=concept,
        label=concept,
        size=50,
        color="#673AB7",  # 진보라색 배경
        shape="circle",   # ← 'dot'에서 'circle'로 변경 (라벨이 안으로 들어감)
        font={
            "size": 40, 
            "color": "#ffffff",  # ← 노드 안 글자이므로 흰색으로 변경
            "face": "Source Sans Pro", 
            "strokeWidth": 0,    # 노드 안에서는 테두리가 없는 게 더 깔끔합니다
        }
    ))
    # 2. 연관 노드 및 관계 선
    for i, row in relation_df.iterrows():
        target_node_id = f"{row['Target']}_{i}"
        nodes.append(Node(
                    id=target_node_id,
                    label=row['Target'],
                    size=16,
                    color="Purple",
                    # 개별 노드에 폰트 설정 추가
                    font={
                        "size": 20,  # 폰트 크기 숫자 (예: 12, 14, 16)
                        "color": "green",  # 글자 색상
                        "face": "Arial",  # 글꼴
                        "align": "center"  # 정렬
                    }
                ))
        edges.append(Edge(
            source=concept,
            target=target_node_id,
            label=" ",
            #label=row['Relation'],
            width=row['Confidence'] * 3,  # 관계 강도를 좀 더 굵게 표현
            color="#D1D1D1",  # 선은 연한 회색으로 처리해 노드를 강조
            type="CURVE_SMOOTH"  # 곡선 처리로 부드러운 느낌
        ))

    # 3. 그래프 설정 (현대적인 다크/라이트 모드 대응)
    config = Config(
        width=500,
        height=500,
        directed=True,
        physics=True,
        nodeHighlightBehavior=True,
        highlightColor="#FF4B4B",
        panAndZoom=True,
        solver="forceAtlas2Based",
        forceAtlas2Based={
            "gravitationalConstant": -150,
            "centralGravity": 0.08,
            "springLength": 180, # 가독성을 위해 간격을 조금 늘림
            "springConstant": 0.05
        }
    )

    return agraph(nodes=nodes, edges=edges, config=config)

def display_styled_table(df):
    st.subheader("📊 상세 관계 분석")
    
    # CSS 강제 정렬 (인덱스 열이 생겨도 숨기도록 CSS 추가)
    st.markdown("""
        <style>
            .stTable td, .stTable th {
                text-align: center !important;
                vertical-align: middle !important;
            }
            /* 혹시 남을지 모르는 인덱스 열(첫 번째 열) 강제 숨김 */
            .stTable thead tr th:first-child { display:none; }
            .stTable tbody tr th:first-child { display:none; }
        </style>
    """, unsafe_allow_html=True)
    
    # 스타일 적용 및 인덱스 숨기기
    styled_df = df.style.hide(axis='index') \
                        .background_gradient(cmap='Purples', subset=['Confidence']) \
                        .set_properties(**{'text-align': 'center', 'font-size': '30px'})
    
    st.table(styled_df)

@st.dialog("🕸️ 온톨로지 지식 그래프 탐색", width="large")
def show_ontology_dialog():
    st.write("분석하고 싶은 핵심 개념(용어)을 입력하면 벡터 DB 기반으로 관계를 분석합니다.")

    # 팝업 내 입력창
    concept_input = st.text_input(
        "핵심 개념 입력",
        placeholder="예: 전자정부법, 수의계약 등",
        key="dialog_concept_input"
    )

    if concept_input:
        with st.spinner("벡터 공간에서 관계를 분석 중입니다..."):
            # 기존에 만드신 추출 함수 호출
            relation_df = extract_ontology_relations(concept_input)

            if isinstance(relation_df, pd.DataFrame):
                tab1, tab2 = st.columns([1.5, 1])
                with tab1:
                    display_styled_table(relation_df)

                with tab2:
                     display_knowledge_graph(concept_input, relation_df)

                # 요약 메시지
                top_relation = relation_df.iloc[0]
                st.success(f"분석 완료: **{concept_input}**은(는) **{top_relation['Target']}**와 가장 밀접합니다.")
            else:
                st.error(relation_df)

    # 닫기 버튼
    if st.button("닫기"):
        st.rerun()

########################################################################################################
# 5.로그인 화면
########################################################################################################
# --- DB 사용자 조회 함수 ---
def verify_user(username, password):
    """DB에서 아이디와 비밀번호가 일치하고 승인(available='Y')된 사용자인지 확인"""
    # 입력받은 비밀번호 해싱
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect('users.db')
    # 데이터를 딕셔너리 형태로 가져오기 위한 설정 (컬럼명으로 접근 가능)
    conn.row_factory = sqlite3.Row 
    c = conn.cursor()
    
    # SQL 쿼리 실행: 아이디, 비밀번호, 승인여부 삼박자가 맞아야 함
    c.execute('''
        SELECT * FROM users 
        WHERE username = ? AND password = ? AND available = 'Y'
    ''', (username, hashed_pw))

    user_row = c.fetchone()
    conn.close()
    
    if user_row:
        # sqlite3.Row 객체를 일반 파이썬 딕셔너리로 변환하여 반환
        return dict(user_row)
    return None

# --- 로그인 UI 함수 ---
def login():
    st.title("🔐 Login System")
    # st.form을 사용하면 엔터키 입력 시 자동으로 submit_button이 눌립니다.
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if username and password:
                # DB에서 사용자 확인
                user_found = verify_user(username, password)
                
                if user_found:
                    st.session_state.logged_in = True
                    st.session_state.user_info = user_found
                    st.success(f"어서오세요, {user_found['name']}님!")
                    st.rerun()  # 페이지 리프레시
                else:
                    # 실패 원인은 보안상 상세히 알리지 않는 것이 관례입니다 (아이디 틀림 vs 비번 틀림)
                    st.error("아이디/비밀번호가 틀렸거나 관리자 승인이 되지 않았습니다.")
            else:
                st.warning("아이디와 비밀번호를 모두 입력해주세요.")


    # 버튼 클릭 시 다이얼로그 함수 실행
    if st.button("➕ 신규 사용자 등록", type="secondary", use_container_width=True):
        show_userapplication_dialog()

#####################################################################################
###############################  main code 시작 ######################################
#####################################################################################

def main_dashboard():
#####################################
# 메인 채팅 화면
#####################################
    st.markdown("""
        <style>
            /* 1. 메인 화면 상단 여백 제거 */
            .block-container {
                padding-top: 1.5rem;
            }

            /* 2. 사이드바 내부 상단 여백 제거 */
            [data-testid="stSidebarUserContent"] {
                padding-top: 1rem; /* 0으로 하면 너무 붙으니 1rem 정도 추천합니다 */
            }

            /* 3. 사이드바 제목(h1) 자체의 여백 조절 */
            [data-testid="stSidebarUserContent"] h1 {
                margin-top: -30px; /* 위로 더 끌어올리고 싶을 때 사용 */
                padding-top: 0px;
            }

            # /* (선택) 헤더 숨기기 */
            header {
                visibility: hidden;
                height: 0px;
            }
        </style>
    """, unsafe_allow_html=True)
    st.markdown(
        f"<h2 style='text-align: center;'> 지식중심 & 업무중심의 사업관리 RAG </h2>",
        unsafe_allow_html=True
    )
# --- 3. 사이드바 구성 ---
    with st.sidebar:
        user = st.session_state.user_info
        # 로그인 정보 출력
        st.header("🌸 사용자 정보")
        if st.button(f"{'&nbsp;'*10}{user['name']}{'&nbsp;'*5}|{'&nbsp;'*10}Logout{'&nbsp;'*5}", type="secondary",use_container_width=True ):
            st.session_state.clear()
            st.rerun()
        with st.container(border=True):
            search_option = st.radio(
                # f"{'&nbsp;' * 5}⤷  검색 방법 선택",
                '🪄 RAG 검색 설정',
                ("Hybrid (Vector + BM25)", "Vector(유사도) Only", "BM25(키워드) Only"),
                index=0
            )
        k_value = st.slider(f"{'&nbsp;' * 5}⤷ 검색할 문서 청크 개수 (기본: {DEFAULT_K_VALUE})",
                            min_value=5, max_value=15, value=DEFAULT_K_VALUE)

         #####################################
        # DB상태 표시
        #####################################
        st.header("‍♻️ DB정보 관리")
        if st.session_state.vectorstore:
            all_docs = st.session_state.vectorstore.docstore._dict.values()
            unique_files = set([doc.metadata.get('source') for doc in all_docs if doc.metadata.get('source')])
            doc_count = len(unique_files)
            chunk_count = len(all_docs)

            with st.expander("DB 자세히 보기 / 닫기", expanded =False if st.session_state.user_info['role'] == 'SystemAdmin' else True):
                st.write(f"학습된 문서 수:  {doc_count}개")
                st.write(f"전체 청크 수: {chunk_count}개")
                if unique_files:
                    # --- 이 부분이 콤보박스로 수정됩니다 ---
                    selected_file_from_db = st.selectbox(
                        "🔍 임베딩된 문서 선택:",  # 콤보박스의 레이블
                        options=unique_files,  # 드롭다운에 표시될 파일 목록
                        index=0 if unique_files else None,  # 첫 번째 파일을 기본으로 선택, 없으면 None
                        key="embedded_file_selector"  # 고유한 키 부여
                    )
        else:
            st.info("DB에 로드된 문서가 없습니다.")
        # --- DB 상태 표시 끝 ---

        if st.session_state.vectorstore:
            if st.button("🕸️ 온톨로지 탐색기 열기", type="primary",use_container_width=True):
                show_ontology_dialog()

                
############  관리자 role 만 사용 
        ## 파일 업로드
        ############
        if st.session_state.user_info['role'] == 'SystemAdmin':                
            st.header("‍👥 관리자 Play")
            uploaded_file = st.file_uploader(f"{'&nbsp;'*5} ⤷{'&nbsp;'} 문서를 등록하세요.", type="pdf")
            st.session_state.uploaded_files_registry = load_uploaded_files_registry()
            if uploaded_file:
                file_content = uploaded_file.getvalue()
                current_file_hash = calculate_file_hash(file_content)
                save_path = os.path.join(UPLOAD_PATH, uploaded_file.name)

                if st.button(f"{'&nbsp;'*23}임베딩 시작{'&nbsp;'*23}", type="primary",  key="start_update_embed",use_container_width=True ):
                    if uploaded_file.name in st.session_state.uploaded_files_registry:
                        if st.session_state.uploaded_files_registry[uploaded_file.name] == current_file_hash:
                            st.sidebar.error(f"'{uploaded_file.name}' (동일 내용) 파일은 이미 임베딩되어 있습니다.")
                            st.stop()
                        else:
                            st.sidebar.warning(f"'{uploaded_file.name}' 파일의 내용이 변경되어 업데이트를 진행합니다.")
                            chunks = process_pdf(uploaded_file)
                            # print(f"반환된 청크 갯수: {len(chunks)}")
                            # for k, chunk in enumerate(chunks):
                            #     print('#' * 100)
                            #     print(f"번호: {k + 1} / {len(chunks)}")
                            #     print(f"chunk.page_content: {chunk.page_content}")
                            #     print(f"chunk.metadata: {chunk.metadata}")
                            update_vectorstore(chunks, uploaded_file.name)
                            del st.session_state.uploaded_files_registry[uploaded_file.name]
                            st.session_state.uploaded_files_registry[uploaded_file.name] = current_file_hash
                            save_uploaded_files_registry(st.session_state.uploaded_files_registry)
                            st.success(f"'{uploaded_file.name}' 임베딩 완료!")
                            st.rerun()

                    else:
                        st.sidebar.info(f"'{uploaded_file.name}' 파일은 처음 작업입니다.")
                        chunks = process_pdf(uploaded_file)
                        # print(f"반환된 청크 갯수: {len(chunks)}")
                        # for k, chunk in enumerate(chunks):
                        #     print('#' * 100)
                        #     print(f"번호: {k + 1} / {len(chunks)}")
                        #     print(f"chunk.page_content: {chunk.page_content}")
                        #     print(f"chunk.metadata: {chunk.metadata}")

                        update_vectorstore(chunks, uploaded_file.name)
                        st.session_state.uploaded_files_registry[uploaded_file.name] = current_file_hash
                        save_uploaded_files_registry(st.session_state.uploaded_files_registry)
                        st.success(f"'{uploaded_file.name}' 임베딩 완료!")
                        st.rerun()

            #####################################
            # DB 삭제 버튼 (첫 번째 클릭 시 확인 요청)
            #####################################
            if "confirm_delete_db" not in st.session_state:
                st.session_state.confirm_delete_db = False

            # 1. 삭제 트리거 버튼
            if st.button(f"⤷ DB 전체 삭제{'&nbsp;' * 26}", type="secondary", use_container_width=True):
                st.session_state.confirm_delete_db = True

            # 2. 확인 UI 영역 (empty 컨테이너 생성)
            delete_container = st.empty()

            if st.session_state.confirm_delete_db:
                # empty 컨테이너 안에서 UI를 구성합니다.
                with delete_container.container():
                    st.warning("⚠️ 모든 임베딩된 데이터, 파일 정보 및 채팅 이력이 영구적으로 삭제됩니다. 계속하시겠습니까?")
                    col1, col2 = st.columns([5, 5])

                    with col1:
                        if st.button("✅ YES!", type="primary", key="confirm_delete_btn", use_container_width=True):
                            reset_database()  # 실제 삭제 함수 호출
                            st.success("삭제되었습니다!")  # (선택 사항) 결과 표시
                            st.session_state.confirm_delete_db = False
                            delete_container.empty()  # 즉시 컨테이너 안의 모든 UI를 삭제
                            st.rerun()  # 전체 상태 동기화

                    with col2:
                        if st.button("❌ 취소", type="secondary", key="cancel_delete_btn", use_container_width=True):
                            st.session_state.confirm_delete_db = False
                            delete_container.empty()  # 즉시 컨테이너 안의 모든 UI를 삭제

            if  st.button(f"사용자 승인/삭제 처리", type="primary", use_container_width=True):
                st.header("‍🕵 사용자 관리")
                admin_page()
            

                # 버튼 클릭 시 다이얼로그 함수 실행

       
    # 대화 이력 초기화
    if "chat_history" not in st.session_state:
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "rb") as f:
                st.session_state.chat_history = pickle.load(f)
        else:
            st.session_state.chat_history = []


     # 대화 이력 출력
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "source" in message:
                with st.expander("참조 문서 확인"):
                    # st.write(message["source"])
                    st.markdown('\n\n'.join(message["source"][:-1]))

    # 질의 입력 (DB가 있을 때만 활성화)
    if st.session_state.vectorstore:
        if user_query := st.chat_input("문서에 대해 궁금한 점을 물어보세요"):
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):

                with st.spinner("답변을 생성 중입니다..."):
                    if search_option == "Hybrid (Vector + BM25)":
                        k_value = max(int(k_value/2), 2)

                    if search_option == "Vector(유사도) Only":
                        docs_with_scores = st.session_state.vectorstore.similarity_search_with_score(user_query, k=k_value)
                        docs_for_context = [doc for doc, _score in docs_with_scores]
                        context = "\n\n".join([d.page_content for d in docs_for_context])

                        formatted_sources = []
                        for doc, score in docs_with_scores:  # docs_with_scores에는 이미 점수 유무 정보가 포함
                            source_name = doc.metadata.get("source", "알 수 없는 파일")
                            page_num = doc.metadata.get("page", "N/A")

                            formatted_sources.append(f"- **유사도:** `{score:,.4f}`\n")
                            formatted_sources.append(f"- **참고문서:** `{source_name}` (Page: {page_num})\n")
                            formatted_sources.append(f"- **내용 (일부):** \n\n{doc.page_content[:200]}...")
                            formatted_sources.append("---")

                    elif search_option == "BM25(키워드) Only":
                        all_docs_for_bm25 = []
                        if st.session_state.vectorstore and st.session_state.vectorstore.docstore:
                            all_docs_for_bm25 = list(st.session_state.vectorstore.docstore._dict.values())
                        if all_docs_for_bm25:
                            bm25_retriever = BM25Retriever.from_documents(all_docs_for_bm25)
                            bm25_retriever.k = k_value
                        docs = bm25_retriever.invoke(user_query)
                        context = "\n\n".join([d.page_content for d in docs])

                        formatted_sources = []
                        for doc in docs:
                            source_name = doc.metadata.get("source", "알 수 없는 파일")
                            page_num = doc.metadata.get("page", "N/A")

                            formatted_sources.append(f"- **키워드 검색결과**\n")
                            formatted_sources.append(f"- **참고문서:** `{source_name}` (Page: {page_num})\n")
                            formatted_sources.append(f"- **내용 (일부):** \n\n{doc.page_content[:200]}...")
                            formatted_sources.append("---")

                    elif search_option == "Hybrid (Vector + BM25)":
                        docs_with_scores = st.session_state.vectorstore.similarity_search_with_score(user_query, k=k_value)
                        docs = [doc for doc, _score in docs_with_scores]

                        all_docs_for_bm25 = []
                        if st.session_state.vectorstore and st.session_state.vectorstore.docstore:
                            all_docs_for_bm25 = list(st.session_state.vectorstore.docstore._dict.values())
                        if all_docs_for_bm25:
                            bm25_retriever = BM25Retriever.from_documents(all_docs_for_bm25)
                            bm25_retriever.k = k_value
                        bm25_docs = bm25_retriever.invoke(user_query)

                        docs.extend(bm25_docs)


                        formatted_sources = []
                        for doc, score in docs_with_scores:  # docs_with_scores에는 이미 점수 유무 정보가 포함
                            source_name = doc.metadata.get("source", "알 수 없는 파일")
                            page_num = doc.metadata.get("page", "N/A")
                            formatted_sources.append(f"- **유사도:** `{score:,.4f}`\n")
                            formatted_sources.append(f"- **참고문서:** `{source_name}` (Page: {page_num})\n")
                            formatted_sources.append(f"- **내용 (일부):** \n\n{doc.page_content[:200]}...")
                            formatted_sources.append("---")

                        for doc in bm25_docs:
                            source_name = doc.metadata.get("source", "알 수 없는 파일")
                            page_num = doc.metadata.get("page", "N/A")
                            formatted_sources.append(f"- **키워드 검색결과**\n")
                            formatted_sources.append(f"- **참고문서:** `{source_name}` (Page: {page_num})\n")
                            formatted_sources.append(f"- **내용 (일부):** \n\n{doc.page_content[:200]}...")
                            formatted_sources.append("---")

                        context = "\n\n".join([d.page_content for d in docs])


                    full_prompt = f"""
                    당신은 **정보화 사업 전문 법률 자문 및 실무 지원 전문가'**입니다.
                    정보화 사업 추진 담당자가 반드시 숙지해야 할 관련 법령(전자정부법, SW진흥법, 개인정보보호법, 정보통신망법 등) 및 내부 규정을 
                    법률가의 엄밀함과 베테랑 실무자의 관점으로 분석하고, 명확하고 실용적인 답변을 제공해야 합니다. 관련 정보가 없을시 원하는 질문에 대한
                    답변이 존재하지 않는다고 해야합니다. 그리고 답변은 한글로 답해주세요. 

                    **[답변 원칙]**

                    1. **정의 기반 설명**: 답변은 항상 질문과 관련된 핵심 용어의 **법적/규정상 정의**에서 시작합니다. 단순 정의 나열이 아닌, 해당 정의가 정보화 사업에 미치는 영향을 간략히 설명합니다.
                    2. **사업 단계별 적용**: 법령이 정보화 사업의 **기획, 설계, 개발, 구축, 운영, 유지보수 단계 중 어느 단계에** 주로 적용되는지 명확히 제시합니다. 각 단계별 고려사항을 함께 설명합니다.
                    3. **근거 명확성**: 답변은 반드시 제공된 **[컨텍스트] 내의 정보만을 사용**합니다. 근거가 없는 내용은 "죄송합니다. 제공된 문서 및 규정 내에서는 해당 정보를 찾을 수 없습니다."라고 답변합니다. 출처(법령 조항, 규정 명칭)를 명시하여 신뢰도를 높입니다.
                    4. **시각적 강조 및 구조화**:
                        * 핵심 용어는 **굵게** 처리하고, :red[빨간색 강조] 또는 :blue[파란색 강조] 문법을 사용하여 표시합니다. (예: :red[정보시스템])
                        * 복잡한 비교, 절차, 핵심 요약은 반드시 **마크다운 표(Table)**를 사용하여 정리합니다.
                        * 답변은 **번호 매기기** 또는 **글머리 기호**를 사용하여 논리적으로 구성합니다.
                    5. **위험 관리**: 법규 위반 가능성이 있는 상황을 식별하고, 잠재적 위험 및 대응 방안을 제시합니다.
                    6. **최신성**: 관련 법규 및 규정의 최신 개정 사항을 반영합니다. (컨텍스트에 최신 정보가 없을 경우, "제공된 컨텍스트는 최신 정보가 아닐 수 있습니다. 관련 법규의 최신 개정 사항을 확인하시기 바랍니다."라고 명시합니다.)

                    **[컨텍스트]**

                    {context}

                    **질문:** {user_query}

                    **[답변 구조]**

                    1. **관련 규정상 주요 용어 정의**: (핵심 개념을 정의하되, 주요 단어는 **굵게** 표시하고, 정보화 사업에 미치는 영향 간략히 설명)
                    2. **질문에 대한 규정 기반 답변**:
                        * (내용을 충실히 반영하여 설명하며, 사업 단계별 적용 여부 명시)
                        * **[규정 요약 표]**: 핵심 내용을 요약하여 표 형태로 제시 (사업 단계, 관련 법령, 주요 내용, 유의사항 등을 포함)
                    3. **사업 담당자를 위한 실무 유의사항**:
                        * (실무적 조언을 적되, 주의사항은 :red[빨간색 강조]로 표시하고, 위반 시 발생할 수 있는 법적 책임 명시)
                    4. **잠재적 위험 및 대응 방안**: (법규 위반 가능성이 있는 상황을 식별하고, 위험 완화 방안 제시)
                    """
                    # 4. LLM 호출: st.session_state.llm.invoke() 사용
                    # 이전에 st.session_state에 로드된 Ollama 객체를 직접 사용합니다.
                    # print("-"*50)
                    # print(f"최종 프롬프트를 전달했습니다.")

                    # llm = ChatOllama(model=LLM_MODEL)

                    response_stream = LLM_MODEL.stream(full_prompt) # 전역 변수 LLM_MODEL 사용
                    answer = st.write_stream(response_stream)

                    # 이력 저장
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,  # answer.content
                        "source": formatted_sources
                    })
                    save_chat_history()
                    st.rerun()


    else:
        st.info("왼쪽 사이드바에서 PDF 파일을 업로드하고 학습을 시작해주세요.")
    # st.write(f"[사업관리 R/AG 사용 모델 /*:&nbsp; 🧠LLM 모델:&nbsp; {LLM_MODEL}&nbsp;&nbsp;  🧮임베딩 모델:&nbsp; {EMBEDDING_MODEL}:&nbsp; 💡유사도: 벡터거리*/ ]")
if not st.session_state.logged_in:
    login()
else:
    HISTORY_PATH = os.path.join(HISTORY, f"chat_history_{st.session_state.user_info['username']}.pkl")
    main_dashboard()
