import streamlit as st
import re
import logging
import subprocess
import sys
from typing import Dict, Optional
from io import BytesIO

# Check and install required packages
def install_missing_packages():
    required_packages = {
        "python-docx": "docx",
        "pypdf": "pypdf"
    }
    
    missing_packages = []
    
    # Check which packages are missing
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    # Install missing packages
    if missing_packages:
        st.warning(f"Installing required packages: {', '.join(missing_packages)}")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                st.success(f"Successfully installed {package}")
            except Exception as e:
                st.error(f"Failed to install {package}: {str(e)}")
                st.error("Please install it manually with: pip install " + package)
    
    return len(missing_packages) == 0

# Install packages if needed
packages_ready = install_missing_packages()

# Now import the required packages
if packages_ready:
    try:
        from docx import Document
        from pypdf import PdfReader
    except ImportError:
        st.error("There was an issue importing the required libraries.")
        Document = None
        PdfReader = None
else:
    # Provide dummy implementations for development/testing
    Document = None
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
    
    def read_text_file(self, file) -> Optional[str]:
        """Extract text from a plain text file"""
        try:
            content = file.read().decode('utf-8')
            return content
        except Exception as e:
            self.logger.error(f"Error reading text file: {str(e)}")
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
        """Extract skills using keyword matching"""
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
    
    def extract_education(self, text: str) -> list:
        """Extract education information using patterns"""
        education = []
        # Look for common degree patterns
        degree_patterns = [
            r'\b(Ph\.?D\.?|Doctor of Philosophy)\b',
            r'\b(M\.?S\.?|Master of Science|MBA|Master of Business Administration)\b',
            r'\b(B\.?S\.?|B\.?A\.?|Bachelor of Science|Bachelor of Arts)\b',
            r'\b(Associate\'?s? Degree|A\.?A\.?|A\.?S\.?)\b'
        ]
        
        for pattern in degree_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get surrounding context (50 characters before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                education.append(context)
        
        return education

    def parse_resume(self, uploaded_file) -> Dict:
        """Main method to parse resume and return structured data"""
        self.logger.info(f"Starting to parse resume: {uploaded_file.name}")
        
        text = None
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        if file_ext == 'pdf':
            text = self.read_pdf(uploaded_file)
        elif file_ext == 'docx':
            text = self.read_docx(uploaded_file)
        elif file_ext == 'txt':
            text = self.read_text_file(uploaded_file)
        else:
            return {"error": f"Unsupported file format: {file_ext}"}
        
        if not text:
            return {"error": "Failed to read resume file"}

        return {
            "email": self.extract_email(text),
            "phone": self.extract_phone(text),
            "skills": self.extract_skills(text),
            "education": self.extract_education(text),
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
        
        if data.get("education"):
            doc.add_heading('Education', level=1)
            for edu in data.get("education"):
                doc.add_paragraph(f"• {edu}")
            
        if data.get("raw_text"):
            doc.add_heading('Original Resume Text', level=1)
            doc.add_paragraph(data["raw_text"])
        
        # Save document to BytesIO object
        doc_io = BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        return doc_io


def main():
    st.set_page_config(
        page_title="Resume Parser", 
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Resume Parser App")
    st.write("""
    Upload your resume (PDF, DOCX, or TXT) to extract key information.
    The app will identify contact details, skills, education, and provide a downloadable analysis report.
    """)
    
    # File uploader with multiple file types
    uploaded_file = st.file_uploader(
        "Choose a resume file", 
        type=["pdf", "docx", "txt"],
        help="Upload your resume in PDF, DOCX, or TXT format"
    )

    if uploaded_file is not None:
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{round(uploaded_file.size / 1024, 2)} KB",
            "File type": uploaded_file.type
        }
        
        st.write("### File Details")
        for key, value in file_details.items():
            st.write(f"**{key}:** {value}")
        
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
                        st.markdown("#### 📇 Contact Information")
                        st.write(f"📧 Email: {data.get('email', 'Not found')}")
                        st.write(f"📱 Phone: {data.get('phone', 'Not found')}")
                    
                    with col2:
                        st.markdown("#### 🧠 Skills")
                        if data.get("skills"):
                            skill_cols = st.columns(3)
                            for i, skill in enumerate(data.get("skills", [])):
                                skill_cols[i % 3].write(f"✓ {skill}")
                        else:
                            st.write("No common skills detected")
                    
                    # Display education
                    if data.get("education"):
                        st.markdown("#### 🎓 Education")
                        for edu in data.get("education"):
                            st.write(f"• {edu}")
                    
                    # Create download button for Word document
                    doc_bytes = parser.create_word_document(data)
                    if doc_bytes:
                        st.markdown("### 📥 Download Report")
                        st.write("Get a complete analysis of your resume as a Word document:")
                        st.download_button(
                            label="Download Analysis Report",
                            data=doc_bytes,
                            file_name="resume_analysis.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    
                    # Add a text area to display raw text if needed
                    with st.expander("View Raw Text"):
                        st.text_area("Resume Content", data.get("raw_text", ""), height=300)
                    
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")
                st.error("Please ensure you have the required libraries installed.")
                st.code("pip install streamlit python-docx pypdf")


if __name__ == "__main__":
    main()
