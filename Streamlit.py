import streamlit as st

# Set page config BEFORE anything else
st.set_page_config(
    page_title="Resume Parser", 
    page_icon="📄",
    layout="wide"
)

import logging
import subprocess
import sys
import re
from datetime import datetime
from typing import Dict, Optional
from io import BytesIO
from docx import Document
from pypdf import PdfReader
from docx.shared import Pt


# Install missing packages
REQUIRED_PACKAGES = {
    "python-docx": "docx",
    "pypdf": "pypdf"
}

missing = []
for pkg, imp in REQUIRED_PACKAGES.items():
    try:
        __import__(imp)
    except ImportError:
        missing.append(pkg)

if missing:
    for pkg in missing:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        except Exception as e:
            st.error(f"Please manually install {pkg} with pip install {pkg}")
            logging.error(f"Error installing {pkg}: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler()
    ]
)

class ResumeParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.common_skills = {"python", "java", "javascript", "typescript", "html", "css", "sql", "nosql", 
                               "react", "angular", "vue", "node.js", "django", "flask", "express", "spring",
                               "docker", "kubernetes", "aws", "azure", "gcp", "git", "agile", "scrum", "jira",
                               "jenkins", "ci/cd", "rest api", "graphql", "mongodb", "mysql", "postgresql", 
                               "oracle", "data analysis", "machine learning", "deep learning", "ai", "nltk",
                               "pandas", "numpy", "tensorflow", "pytorch", "keras", "scikit-learn", "excel", 
                               "powerpoint", "word", "tableau", "power bi", "linux", "windows", "macos", 
                               "networking", "security"}

    def read_pdf(self, file) -> Optional[str]:
        try:
            reader = PdfReader(file)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            return text
        except Exception as e:
            self.logger.error(f"PDF read error: {e}")
            return None

    def read_docx(self, file) -> Optional[str]:
        try:
            doc = Document(file)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            self.logger.error(f"DOCX read error: {e}")
            return None

    def read_text_file(self, file) -> Optional[str]:
        try:
            return file.read().decode('utf-8')
        except Exception as e:
            self.logger.error(f"Text read error: {e}")
            return None

    def extract_email(self, text: str) -> Optional[str]:
        match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        return match.group(0) if match else None

    def extract_phone(self, text: str) -> Optional[str]:
        match = re.search(r'(\+?\d{1,4}[-\s.]?)?(\(?\d{2,4}\)?[-\s.]?)?\d{3,5}[-\s.]?\d{4,6}', text)
        return match.group(0) if match else None

    def extract_skills(self, text: str) -> list:
        text = text.lower()
        return [skill for skill in self.common_skills if re.search(rf'\b{re.escape(skill)}\b', text)]

    def extract_education(self, text: str) -> list:
        patterns = [
            r'\b(Ph\\.?D\\.?|Doctor of Philosophy)\b',
            r'\b(M\\.?S\\.?|MBA|Master of [A-Za-z]+)\b',
            r'\b(B\\.?S\\.?|B\\.?A\\.?|Bachelor of [A-Za-z]+)\b',
            r'\b(Associate\'s? Degree|A\\.?A\\.?|A\\.?S\\.?)\b'
        ]
        matches = []
        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                start, end = max(0, match.start()-50), min(len(text), match.end()+50)
                matches.append(text[start:end].strip())
        return matches

    def create_word_report(self, data: Dict) -> BytesIO:
        try:
            template_path = "template.docx"  # Assuming it's in the same directory as your Streamlit script
            doc = Document(template_path)
    
            replacements = {
                "{{email}}": data.get("email", "N/A"),
                "{{phone}}": data.get("phone", "N/A"),
                "{{skills}}": ", ".join(data.get("skills", [])) or "No common skills detected",
                "{{education}}": "\n".join(f"• {edu}" for edu in data.get("education", [])) or "N/A"
            }
    
            for paragraph in doc.paragraphs:
                for key, val in replacements.items():
                    if key in paragraph.text:
                        paragraph.text = paragraph.text.replace(key, val)
                        for run in paragraph.runs:
                            run.font.size = Pt(11)  # Optional: format font size
    
            buf = BytesIO()
            doc.save(buf)
            buf.seek(0)
            return buf
    
        except Exception as e:
            self.logger.error(f"Template report creation failed: {e}")
            return None

@st.cache_resource
def get_parser():
    return ResumeParser()

def main():
    #st.set_page_config(page_title="Resume Parser", page_icon="📄", layout="wide")
    st.title("📄 Resume Parser App")
    st.write("Upload a resume (PDF, DOCX, TXT) to extract contact info, skills, and education.")

    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])

    if uploaded_file:
        st.info(f"File uploaded: {uploaded_file.name}")
        parser = get_parser()
        ext = uploaded_file.name.split('.')[-1].lower()

        if ext == "pdf":
            text = parser.read_pdf(uploaded_file)
        elif ext == "docx":
            text = parser.read_docx(uploaded_file)
        elif ext == "txt":
            text = parser.read_text_file(uploaded_file)
        else:
            st.error("Unsupported file format")
            return

        if not text:
            st.error("Could not read the file.")
            return

        data = {
            "email": parser.extract_email(text),
            "phone": parser.extract_phone(text),
            "skills": parser.extract_skills(text),
            "education": parser.extract_education(text),
            "raw_text": text
        }

        st.success("Resume parsed successfully!")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📇 Contact Info")
            st.write(f"📧 {data['email'] or 'Not found'}")
            st.write(f"📱 {data['phone'] or 'Not found'}")
        with col2:
            st.subheader("🧠 Skills")
            if data['skills']:
                for skill in data['skills']:
                    st.markdown(f"- {skill}")
            else:
                st.write("No common skills found")

        if data['education']:
            st.subheader("🎓 Education")
            for edu in data['education']:
                st.write(f"• {edu}")

        st.subheader("📥 Download Report")
        doc = parser.create_word_report(data)
        st.download_button(
            label="Download Word Report",
            data=doc,
            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        with st.expander("View Raw Resume Text"):
            st.code(text, language='text')

if __name__ == "__main__":
    main()
