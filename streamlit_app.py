# 1. Import libraries
import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv
import os
from fpdf import FPDF
import unicodedata

# 2. Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 3. Functions
def extract_text_from_pdf(file):
    """Extracts text from uploaded PDF."""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_name(text):
    """Tries to extract user's name from the beginning of the resume."""
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if len(line.split()) >= 2 and all(word[0].isupper() for word in line.split() if word.isalpha()):
            return line
    return "User"

def clean_text(text):
    """Cleans text to avoid encoding problems when generating PDF."""
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = unicodedata.normalize('NFKD', text).encode('latin-1', 'ignore').decode('latin-1')
    return text

def text_to_pdf(text):
    """Generates a safe PDF for download."""
    text = clean_text(text)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    return pdf.output(dest='S').encode('latin-1')

def analyze_resume(text, lang="en"):
    """Sends text to AI model for resume analysis."""
    prompt = PROMPT_ANALYSIS_EN.format(text=text) if lang == "en" else PROMPT_ANALYSIS_PT_BR.format(text=text)
    response = model.generate_content(prompt)
    return response.text

# 4. Prompts
PROMPT_ANALYSIS_EN = """
You are a Human Resources specialist focused on hiring Data Scientists.
Carefully review the following CV and respond with:

1. Score from 0 to 10 for:
   - Clarity
   - Impact
   - Suitability for Data Science roles

2. Identify key strengths.

3. Identify main weaknesses.

4. Provide concrete suggestions for improvement.

5. Is the CV ready for international job applications?

Here is the CV:
{text}
"""

PROMPT_ANALYSIS_PT_BR = """
Você é um especialista em Recursos Humanos focado na contratação de Cientistas de Dados.
Analise cuidadosamente o currículo abaixo e responda:

1. Dê uma nota de 0 a 10 para:
   - Clareza
   - Impacto
   - Adequação para vagas de Ciência de Dados

2. Principais pontos fortes.

3. Principais pontos de melhoria.

4. Sugestões práticas de como melhorar o currículo.

5. O currículo está pronto para candidaturas internacionais?

Aqui está o currículo:
{text}
"""

# 5. Initialize model
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

# 6. Streamlit App - Page Setup + Custom Theme
st.set_page_config(
    page_title="CV Analyzer AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Theme (background, fonts, buttons)
st.markdown(
    """
    <style>
    body {
        background-color: #f5f7fa;
    }
    .stApp {
        background-color: #f5f7fa;
    }
    h1, h2, h3, h4, h5 {
        color: #333333;
    }
    .css-1d391kg {
        color: #0066cc;
    }
    .stButton>button {
        background-color: #0066cc;
        color: white;
        border: none;
        padding: 0.6em 1.2em;
        font-size: 1em;
        border-radius: 8px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #004999;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📄 Resume Analyzer with AI")
st.write("Upload your CV and get an analysis in both **English** 🇬🇧 and **Brazilian Portuguese** 🇧🇷.")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload CV", "🇬🇧 English Review", "🇧🇷 Revisão em Português (Brasil)"])

# Global variables
pdf_text = None
name = "User"

with tab1:
    st.header("Upload your CV here")
    uploaded_file = st.file_uploader("Choose your PDF file", type="pdf")

    if uploaded_file is not None:
        pdf_text = extract_text_from_pdf(uploaded_file)
        name = extract_name(pdf_text).replace(" ", "_")
    
    st.markdown("---")
    with st.expander("❓ How to download your LinkedIn Resume (Click to expand)"):
        st.image("images/linkedin_example.png", caption="Example of downloading your LinkedIn resume", use_container_width=True)
        st.info("Go to LinkedIn → Profile → More → 'Save to PDF' and upload it here.")

with tab2:
    if pdf_text:
        with st.spinner(f'Analyzing {name.replace("_", " ")}\'s resume in English...'):
            english_review = analyze_resume(pdf_text, lang="en")

        st.header(f"🇬🇧 English Resume Review for {name.replace('_', ' ')}")
        st.write(english_review)

        english_pdf = text_to_pdf(english_review)

        st.download_button(
            label="📥 Download English Review as PDF",
            data=english_pdf,
            file_name=f"{name}_English_Review.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Please upload your PDF in the 'Upload CV' tab first.")

with tab3:
    if pdf_text:
        with st.spinner(f'Analisando o currículo de {name.replace("_", " ")} em português brasileiro...'):
            portuguese_review = analyze_resume(pdf_text, lang="pt")

        st.header(f"🇧🇷 Revisão do Currículo em Português (Brasil) para {name.replace('_', ' ')}")
        st.write(portuguese_review)

        portuguese_pdf = text_to_pdf(portuguese_review)

        st.download_button(
            label="📥 Baixar Revisão em PDF (Português-BR)",
            data=portuguese_pdf,
            file_name=f"{name}_Revisao_PTBR.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Por favor, envie seu PDF na aba 'Upload CV' primeiro.")
