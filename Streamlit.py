import streamlit as st
import re
import logging
from typing import Dict, Optional
from io import BytesIO

# Try importing the required libraries, with graceful fallbacks
try:
    from docx import Document
except ImportError:
    st.error("python-docx is not installed. Please install it with: pip install python-docx")
    Document = None

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        st.error("pypdf is not installed. Please install it with: pip install pypdf")
        PdfReader = None


class ResumeParser:
    def __init__(self):
        """Initialize the resume parser with logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Define common skills as a class attribute
        self.common_skills = {
            "python", "java", "javascript", "typescript", "html", "css", "sql", "nosql", "react", 
            "angular", "vue", "node.js", "django", "flask", "express", "spring", "docker",
            "kubernetes", "aws", "azure", "gcp", "git", "agile", "scrum", "jira", "jenkins",
            "ci/cd", "rest api", "graphql", "mongodb", "mysql", "postgresql", "oracle", 
            "data analysis", "machine learning", "deep learning", "ai", "nltk", "pandas",
            "numpy", "tensorflow", "pytorch", "keras", "scikit-learn", "excel", "powerpoint",
            "word", "tableau", "power bi", "linux", "windows", "macos", "networking", "security"
        }

    def read_pdf(self, file) -> Optional[str]:
        """Extract text from PDF file"""
        if PdfReader is None:
            return "PDF reader library not available. Please install pypdf."
        
        try:
            reader = PdfReader(file)
            text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
            return text
        except Exception as e:
            self.logger.error(f"Error reading PDF file: {str(e)}")
            return None

    def read_docx(self, file) -> Optional[str]:
        """Extract text from DOCX file"""
        if Document is None:
            return "DOCX reader library not available. Please install python-docx."
            
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
        """Extract skills using keyword matching instead of NLP"""
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Find all skills that appear in the text
        found_skills = []
        for skill in self.common_skills:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
                
        return found_skills

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
        if Document is None:
            st.error("python-docx is required for creating Word documents")
            return None
            
        doc = Document()
        doc.add_heading('Resume Analysis Report', 0)
        
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


def main():
    st.set_page_config(page_title="Resume Parser", page_icon="📄")
    
    st.title("Resume Parser App")
    st.write("""
    Upload your resume (PDF or DOCX) to extract key information.
    The app will identify contact details and skills, and provide a downloadable analysis report.
    """)
    
    # Display installation instructions
    with st.expander("Installation Requirements"):
        st.code("""
        pip install streamlit python-docx pypdf
        streamlit run app.py
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
                    if doc_bytes:
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
                st.error("Make sure you have installed the required packages: python-docx and pypdf")


if __name__ == "__main__":
    main()
