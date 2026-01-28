import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
import os
from dotenv import load_dotenv
import json
import streamlit.components.v1 as components
import math

load_dotenv()

st.set_page_config(page_title="AI Study Buddy", page_icon="🎓", layout="wide")

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ API Key not found! Please check your .env file.")
    st.stop()

genai.configure(api_key=api_key)

def get_gemini_response(prompt, content=""):
    model = genai.GenerativeModel("gemini-3-flash-preview")
    try:
        if content:
            response = model.generate_content(f"{prompt}\n\nContext:\n{content}")
        else:
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error connecting to AI: {e}")
        return None

def extract_text(file):
    reader = pdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

with st.sidebar:
    st.title("🎓 Study Buddy")
    st.success("✅ API Key Connected Securely")
    st.divider()
    st.markdown("### Features")
    st.markdown("- 💬 **Chat:** General doubts")
    st.markdown("- 📄 **PDF:** Summarize & Q/A")
    st.markdown("- 🧠 **Quiz:** Flashcards & Practice")

if "history" not in st.session_state:
    st.session_state.history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "key_terms" not in st.session_state:
    st.session_state.key_terms = ""
if "quiz_list" not in st.session_state:
    st.session_state.quiz_list = []
if "flashcard_list" not in st.session_state:
    st.session_state.flashcard_list = []
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "score_visible" not in st.session_state:
    st.session_state.score_visible = False

tab1, tab2, tab3 = st.tabs(["💬 General Chat", "📄 PDF Study Tool", "🧠 Quiz & Flashcards"])

with tab1:
    st.header("Ask Your Doubts")
    
    for chat in st.session_state.history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])
            
    prompt = st.chat_input("What do you want to learn?")
    if prompt:
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_gemini_response(prompt)
                if response:
                    st.markdown(response)
                    st.session_state.history.append({"role": "assistant", "content": response})

with tab2:
    st.header("Upload & Learn from Documents")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_file:
        if st.button("Process PDF"):
            with st.spinner("Reading file..."):
                st.session_state.pdf_text = extract_text(uploaded_file)
                st.success("PDF Loaded successfully!")
                
    if st.session_state.pdf_text:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Summarize PDF", use_container_width=True):
                with st.spinner("Generating summary..."):
                    st.session_state.summary = get_gemini_response("Summarize this in detailed bullet points.", st.session_state.pdf_text)
        with col2:
            if st.button("🔑 Extract Key Terms", use_container_width=True):
                with st.spinner("Extracting terms..."):
                    st.session_state.key_terms = get_gemini_response("List top 10 technical terms with definitions.", st.session_state.pdf_text)

        if st.session_state.summary:
            st.markdown("### Summary")
            st.markdown(st.session_state.summary)
            st.divider()
            
        if st.session_state.key_terms:
            st.markdown("### Key Terms")
            st.markdown(st.session_state.key_terms)
            st.divider()
            
        q = st.text_input("Ask a question about this PDF")
        if q:
            with st.spinner("Finding answer..."):
                ans = get_gemini_response(f"Answer strictly based on context: {q}", st.session_state.pdf_text)
                if ans:
                    st.markdown(f"**Answer:** {ans}")

with tab3:
    st.header("Practice & Revise")
    
    mode = st.radio("Select Activity:", ["Quiz (MCQ)", "Flashcards"], horizontal=True)
    count = st.number_input("Number of Questions/Cards", min_value=1, max_value=20, value=5)
    
    source = st.radio("Source:", ["Manual Topic", "Uploaded PDF"])
    topic = ""
    
    if source == "Manual Topic":
        topic = st.text_input("Enter Topic (e.g., Python Loops)")
    elif source == "Uploaded PDF" and st.session_state.pdf_text:
        topic = "The uploaded document content"
        
    if st.button(f"Generate {mode}"):
        context = st.session_state.pdf_text if source == "Uploaded PDF" else topic
        
        if mode == "Quiz (MCQ)":
            prompt = f"""
            Create {count} multiple choice questions based on: {context}.
            Return ONLY raw JSON. Format:
            [
                {{"question": "Q1 text", "options": ["A", "B", "C", "D"], "correct": "A"}}
            ]
            """
            res = get_gemini_response(prompt)
            if res:
                clean = res.replace("```json", "").replace("```", "").strip()
                try:
                    st.session_state.quiz_list = json.loads(clean)
                    st.session_state.flashcard_list = [] 
                    st.session_state.score_visible = False
                    st.session_state.quiz_answers = {}
                except:
                    st.error("Error generating quiz. Please try again.")

        else:
            prompt = f"""
            Create {count} flashcards based on: {context}.
            Return ONLY raw JSON. Format:
            [
                {{"front": "Term", "back": "Definition"}}
            ]
            """
            res = get_gemini_response(prompt)
            if res:
                clean = res.replace("```json", "").replace("```", "").strip()
                try:
                    st.session_state.flashcard_list = json.loads(clean)
                    st.session_state.quiz_list = []
                except:
                    st.error("Error generating flashcards.")

    if mode == "Quiz (MCQ)" and st.session_state.quiz_list:
        with st.form("mcq_form"):
            for i, q in enumerate(st.session_state.quiz_list):
                st.write(f"**{i+1}. {q['question']}**")
                st.session_state.quiz_answers[i] = st.radio("Choose:", q['options'], key=f"q{i}", label_visibility="collapsed")
                st.write("---")
            
            submitted = st.form_submit_button("Check Score")
            if submitted:
                st.session_state.score_visible = True

        if st.session_state.score_visible:
            score = 0
            for i, q in enumerate(st.session_state.quiz_list):
                if st.session_state.quiz_answers.get(i) == q['correct']:
                    score += 1
            st.success(f"You scored: {score} / {len(st.session_state.quiz_list)}")
            
            with st.expander("View Correct Answers"):
                for q in st.session_state.quiz_list:
                    st.write(f"**Q:** {q['question']}")
                    st.info(f"**Correct:** {q['correct']}")

    if mode == "Flashcards" and st.session_state.flashcard_list:
        st.write("### 🗂️ Click cards to flip")
        
        cards_html = """
        <style>
            .flashcard-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: center;
                padding: 20px;
                font-family: sans-serif;
            }
            .flashcard {
                background-color: transparent;
                width: 300px;
                height: 200px;
                perspective: 1000px;
                cursor: pointer;
            }
            .flashcard-inner {
                position: relative;
                width: 100%;
                height: 100%;
                text-align: center;
                transition: transform 0.6s;
                transform-style: preserve-3d;
                box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
                border-radius: 10px;
            }
            .flashcard.flipped .flashcard-inner {
                transform: rotateY(180deg);
            }
            .flashcard-front, .flashcard-back {
                position: absolute;
                width: 100%;
                height: 100%;
                -webkit-backface-visibility: hidden;
                backface-visibility: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                border-radius: 10px;
                box-sizing: border-box;
            }
            .flashcard-front {
                background-color: #2b313e;
                color: white;
                border: 2px solid #4a4e69;
            }
            .flashcard-back {
                background-color: #00b4d8;
                color: white;
                transform: rotateY(180deg);
                border: 2px solid #00b4d8;
            }
        </style>
        <div class="flashcard-container">
        """
        
        for card in st.session_state.flashcard_list:
            front_text = card['front'].replace("'", "&#39;")
            back_text = card['back'].replace("'", "&#39;")
            
            cards_html += f"""
            <div class="flashcard" onclick="this.classList.toggle('flipped')">
                <div class="flashcard-inner">
                    <div class="flashcard-front">
                        <h3>{front_text}</h3>
                    </div>
                    <div class="flashcard-back">
                        <p>{back_text}</p>
                    </div>
                </div>
            </div>
            """
            
        cards_html += "</div>"
        
        # Calculate height to prevent scrolling in the iframe
        rows = math.ceil(len(st.session_state.flashcard_list) / 3) 
        height_needed = rows * 250 + 50
        
        components.html(cards_html, height=height_needed, scrolling=True)