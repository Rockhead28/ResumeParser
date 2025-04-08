import streamlit as st
import sys
import subprocess
import os
import logging
import re
import spacy
import tempfile
from typing import Dict, Optional
from docx.api import Document
from pypdf import PdfReader
import base64
from io import BytesIO


class ResumeParser:
    def __init__(self):
        """Initialize the resume parser with NLP model and logging"""
        try:
            # Check if the model is already loaded
            if 'nlp' not in st.session_state:
                with st.spinner('Loading NLP model...'):
                    st.session_state.nlp = spacy.load("en_core_web_sm")
            self.nlp = st.session_state.nlp
        except OSError:
            st.error("Please install the spaCy model: python -m spacy download en_core_web_sm")
            raise

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def read_pdf(self, file) -> Optional[str]:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(file)
            text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
            return text
        except Exception as e:
            self.logger.error(f"Error reading PDF file: {str(e)}")
            return None

    def read_docx(self, file) -> Optional[str]:
        """Extract text from DOCX file"""
        try:
            doc = Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            self.logger.error(f"Error reading DOCX file: {str(e)}")
            return None

    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        phone_pattern = r'(\+\d{1,3}[-.]?)?\s*\(?([0-9]{3})\)?[-.]?\s*([0-9]{3})[-.]?\s*([0-9]{4})'
        match = re.search(phone_pattern, text)
        return match.group(0) if match else None

    def extract_skills(self, text: str) -> list:
        """Extract skills using NLP"""
        doc = self.nlp(text)
        common_skills = {"python", "java", "javascript", "sql", "react", "node.js", "docker",
                         "kubernetes", "aws", "azure", "git", "agile", "scrum"}
        return list({token.text.lower() for token in doc if token.text.lower() in common_skills})

    def parse_resume(self, uploaded_file) -> Dict:
        """Main method to parse resume and return structured data"""
        self.logger.info(f"Starting to parse resume: {uploaded_file.name}")
        
        text = None
        if uploaded_file.name.endswith('.pdf'):
            text = self.read_pdf(uploaded_file)
        elif uploaded_file.name.endswith('.docx'):
            text = self.read_docx(uploaded_file)
        
        if not text:
            return {"error": "Failed to read resume file"}

        return {
            "email": self.extract_email(text),
            "phone": self.extract_phone(text),
            "skills": self.extract_skills(text),
            "raw_text": text
        }

    def create_word_document(self, data: Dict) -> BytesIO:
        """Create a Word document from parsed resume data and return as bytes"""
        doc = Document()
        doc.add_heading('Resume Analysis Report', 0).alignment = 1
        doc.add_heading('Contact Information', level=1)
        if data.get("email"):
            doc.add_paragraph(f'Email: {data["email"]}')
        if data.get("phone"):
            doc.add_paragraph(f'Phone: {data["phone"]}')
        if data.get("skills"):
            doc.add_heading('Skills', level=1)
            doc.add_paragraph(', '.join(data["skills"]))
        if data.get("raw_text"):
            doc.add_heading('Original Resume Text', level=1)
            doc.add_paragraph(data["raw_text"])
        
        # Save document to BytesIO object
        doc_io = BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        return doc_io


def get_download_link(doc_bytes, filename):
    """Generate a link to download the Word document"""
    b64 = base64.b64encode(doc_bytes.getvalue()).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{filename}">Download Analysis Report</a>'


def main():
    st.set_page_config(page_title="Resume Parser", page_icon="📄")
    
    st.title("Resume Parser App")
    st.write("""
    Upload your resume (PDF or DOCX) to extract key information.
    The app will identify contact details and skills, and provide a downloadable analysis report.
    """)
    
    uploaded_file = st.file_uploader("Choose a resume file", type=["pdf", "docx"])

    if uploaded_file is not None:
        with st.spinner('Processing resume...'):
            parser = ResumeParser()
            try:
                data = parser.parse_resume(uploaded_file)
                
                if "error" in data:
                    st.error(data["error"])
                else:
                    # Display parsed data
                    st.subheader("📊 Parsed Resume Data")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Contact Information**")
                        st.write(f"📧 Email: {data.get('email', 'Not found')}")
                        st.write(f"📱 Phone: {data.get('phone', 'Not found')}")
                    
                    with col2:
                        st.markdown("**Skills**")
                        if data.get("skills"):
                            for skill in data.get("skills", []):
                                st.write(f"✓ {skill}")
                        else:
                            st.write("No common skills detected")
                    
                    # Create download link
                    doc_bytes = parser.create_word_document(data)
                    st.markdown("### Download Report")
                    st.write("Download a Word document with the analysis results:")
                    st.download_button(
                        label="Download Analysis Report",
                        data=doc_bytes,
                        file_name="resume_analysis.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")


if __name__ == "__main__":
    main()
