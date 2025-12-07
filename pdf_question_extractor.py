"""
PDF Question Extractor Library
A library for extracting multiple choice questions from PDF files
and saving them to multiple formats (JSON, Excel, CSV, PDF).
"""

import PyPDF2
import pandas as pd
import re
import os
import json
import csv
from datetime import datetime

# Optional imports with error handling
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available. PDF output disabled.")


class PDFQuestionExtractor:
    """Extract multiple choice questions from PDF files"""
    
    # Supported output formats
    SUPPORTED_FORMATS = ['json', 'excel', 'csv', 'pdf']
    
    def __init__(self, pdf_path):
        """Initialize the extractor with a PDF file path
        
        Args:
            pdf_path (str): Path to the PDF file to process
        """
        self.pdf_path = pdf_path
        self.questions = []
    
    @staticmethod
    def sanitize_text(text):
        """Sanitize text to handle special characters properly
        
        Args:
            text (str): Text to sanitize
            
        Returns:
            str: Sanitized text
        """
        if not text:
            return ""
        
        # Convert to string if not already
        text = str(text)
        
        # Replace problematic characters while preserving readability
        replacements = {
            '\x00': '',  # Null character
            '\r\n': '\n',  # Windows line endings
            '\r': '\n',  # Old Mac line endings
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove any remaining control characters except newlines and tabs
        text = ''.join(char for char in text if char == '\n' or char == '\t' or ord(char) >= 32)
        
        return text.strip()
    
    def extract_text_from_pdf(self):
        """Extract text from PDF
        
        Returns:
            str: Extracted text from all pages
        """
        text = ""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    try:
                        # Try to decrypt with empty password
                        pdf_reader.decrypt('')
                        print("PDF was encrypted but successfully decrypted")
                    except Exception as decrypt_error:
                        print(f"Unable to decrypt PDF: {decrypt_error}")
                        print("Please install PyCryptodome: pip install pycryptodome")
                        return text
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        print(f"Processed page {page_num + 1}/{len(pdf_reader.pages)}")
                    except Exception as page_error:
                        print(f"Error extracting text from page {page_num + 1}: {page_error}")
                        
        except Exception as e:
            print(f"Error reading PDF: {e}")
            print("Make sure the file exists and is a valid PDF")
        
        return text
    
    def find_poppler_path(self):
        """Try to find poppler installation
        
        Returns:
            str or None: Path to poppler bin directory if found
        """
        common_paths = [
            r"C:\Program Files\poppler\Library\bin",
            r"C:\Program Files (x86)\poppler\Library\bin",
            r"C:\poppler\Library\bin",
            r"C:\poppler-24.08.0\Library\bin",
            r"C:\Program Files\poppler-24.08.0\Library\bin",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                print(f"Found poppler at: {path}")
                return path
        
        return None
    
    def extract_text_from_images(self):
        """Extract text from PDF pages as images (for image-based questions)
        
        Returns:
            str: Extracted text from OCR
        """
        if not PDF2IMAGE_AVAILABLE or not PYTESSERACT_AVAILABLE:
            print("OCR libraries not available. Skipping OCR extraction.")
            return ""
        
        try:
            # Try to find poppler in common locations
            poppler_path = self.find_poppler_path()
            
            if poppler_path:
                images = convert_from_path(self.pdf_path, poppler_path=poppler_path)
            else:
                # Try without specifying path (if poppler is in PATH)
                images = convert_from_path(self.pdf_path)
            
            ocr_text = ""
            for i, image in enumerate(images):
                print(f"Processing page {i+1} with OCR...")
                ocr_text += pytesseract.image_to_string(image) + "\n"
            return ocr_text
        except Exception as e:
            print(f"Error with OCR: {e}")
            print("\nTo fix this:")
            print("1. Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/")
            print("2. Extract and note the path to the 'bin' folder")
            print("3. Either add it to PATH or specify in the code")
            return ""

    def parse_questions(self, text):
        """Parse questions from extracted text
        
        Args:
            text (str): Extracted text containing questions
        """
        # Split text by question numbers
        question_pattern = r'QUESTION NO:\s*(\d+)'
        questions_raw = re.split(question_pattern, text)
        
        # Process questions (skip first element if empty)
        for i in range(1, len(questions_raw), 2):
            if i+1 < len(questions_raw):
                question_no = questions_raw[i].strip()
                content = questions_raw[i+1]
                
                question_data = self.parse_question_content(question_no, content)
                if question_data:
                    self.questions.append(question_data)
    
    def extract_reference(self, explanation):
        """Extract reference from explanation text
        
        Args:
            explanation (str): Explanation text that may contain a reference
            
        Returns:
            tuple: (cleaned_explanation, reference) where reference is None if not found
        """
        if not explanation:
            return "", None
        
        # Common reference patterns
        reference_patterns = [
            # Pattern 1: "Reference = Source" or "Reference: Source"
            r'Reference\s*[=:]\s*(.+?)(?:\.|$)',
            # Pattern 2: Source at end with page/chapter info
            r'(?:Source|Ref|Citation)\s*[=:]?\s*(.+?)(?:\.|$)',
            # Pattern 3: Domain reference at end
            r'Domain\s+[\d.]+,\s+(?:page|pg\.?)\s+\d+\s+(.+?)(?:\.|$)',
            # Pattern 4: Citation in parentheses at end
            r'\(([^)]+(?:Study Guide|Edition|Chapter|Page)[^)]*)\)\s*\.?\s*$',
            # Pattern 5: Book/Guide reference at end
            r'([A-Z][^.]+(?:Study Guide|Exam|Edition|Objectives)[^.]*?)\.?\s*'
            ]
        """Parse questions from extracted text
        
        Args:
            text (str): Extracted text containing questions
        """
        # Split text by question numbers
        question_pattern = r'QUESTION NO:\s*(\d+)$',
        questions_raw = re.split(question_pattern, text)
        
        # Process questions (skip first element if empty)
        for i in range(1, len(questions_raw), 2):
            if i+1 < len(questions_raw):
                question_no = questions_raw[i].strip()
                content = questions_raw[i+1]
                
                question_data = self.parse_question_content(question_no, content)
                if question_data:
                    self.questions.append(question_data)
    
    def detect_question_type(self, question_statement, options):
        """Detect if question is text-based or image-based
        
        Args:
            question_statement (str): The question text
            options (str): All options combined
            
        Returns:
            str: 'text' or 'image'
        """
        # Check for image indicators in question statement or options
        image_indicators = [
            'image', 'picture', 'diagram', 'figure', 'screenshot',
            'shown below', 'shown above', 'refer to the', 'see the',
            'following image', 'following diagram', 'following figure',
            'exhibit', 'illustration'
        ]
        
        # Combine question statement and all options for checking
        full_text = f"{question_statement} {options}".lower()
        
        # Check if any image indicator is present
        for indicator in image_indicators:
            if indicator in full_text:
                return "image"
        
        # Check if question statement is very short or missing (might indicate image)
        if len(question_statement.strip()) < 20:
            return "image"
        
        return "text"
    
    def parse_question_content(self, question_no, content):
        """Parse individual question content
        
        Args:
            question_no (str): Question number
            content (str): Question content text
            
        Returns:
            dict or None: Parsed question data
        """
        try:
            # Extract question statement (before options)
            question_match = re.search(r'^(.*?)(?=A\.)', content, re.DOTALL)
            question_statement = question_match.group(1).strip() if question_match else ""
            
            # Extract options
            option_a = self.extract_option(content, 'A')
            option_b = self.extract_option(content, 'B')
            option_c = self.extract_option(content, 'C')
            option_d = self.extract_option(content, 'D')
            
            # Extract correct answer
            answer_match = re.search(r'ANSWER:\s*([A-D])', content, re.IGNORECASE)
            correct_answer = answer_match.group(1).upper() if answer_match else ""
            
            # Extract explanation
            explanation_match = re.search(r'Explanation:(.*?)(?=QUESTION NO:|$)', content, re.DOTALL | re.IGNORECASE)
            explanation = explanation_match.group(1).strip() if explanation_match else ""
            
            # Clean up explanation (remove extra whitespace)
            explanation = re.sub(r'\s+', ' ', explanation).strip()
            
            # Extract reference from explanation
            clean_explanation, reference = self.extract_reference(explanation)
            
            # Detect question type
            all_options = f"{option_a} {option_b} {option_c} {option_d}"
            question_type = self.detect_question_type(question_statement, all_options)
            
            # Sanitize all text fields
            return {
                'question_no': self.sanitize_text(question_no),
                'question_type': question_type,
                'question_statement': self.sanitize_text(question_statement),
                'option_A': self.sanitize_text(option_a),
                'option_B': self.sanitize_text(option_b),
                'option_C': self.sanitize_text(option_c),
                'option_D': self.sanitize_text(option_d),
                'correct_answer': self.sanitize_text(correct_answer),
                'explanation': self.sanitize_text(clean_explanation),
                'reference': self.sanitize_text(reference) if reference else ""
            }
        except Exception as e:
            print(f"Error parsing question {question_no}: {e}")
            return None
    
    def extract_option(self, text, option_letter):
        """Extract specific option text
        
        Args:
            text (str): Text containing the option
            option_letter (str): Option letter (A, B, C, or D)
            
        Returns:
            str: Option text
        """
        next_letter = chr(ord(option_letter) + 1)
        pattern = f'{option_letter}\\.\\s*(.*?)(?={next_letter}\\.|ANSWER:|$)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def save_to_excel(self, output_file='questions_output.xlsx', question_type=None):
        """Save questions to Excel file
        
        Args:
            output_file (str): Output filename
            question_type (str): Filter by type ('text', 'image', or None for all)
        """
        if not self.questions:
            print("No questions found to save!")
            return
        
        # Filter questions by type if specified
        if question_type:
            filtered_questions = [q for q in self.questions if q['question_type'] == question_type]
            if not filtered_questions:
                print(f"No {question_type}-based questions found!")
                return
        else:
            filtered_questions = self.questions
        
        # Create DataFrame
        df = pd.DataFrame(filtered_questions)
        
        # Reorder columns
        column_order = ['question_no', 'question_type', 'question_statement', 
                       'option_A', 'option_B', 'option_C', 'option_D', 
                       'correct_answer', 'explanation', 'reference']
        df = df[column_order]
        
        # Save to Excel with proper encoding
        try:
            df.to_excel(output_file, index=False, engine='openpyxl')
            
            # Print summary
            text_count = len(df[df['question_type'] == 'text'])
            image_count = len(df[df['question_type'] == 'image'])
            
            print(f"[OK] Successfully saved {len(filtered_questions)} questions to {output_file}")
            if not question_type:
                print(f"  - Text-based questions: {text_count}")
                print(f"  - Image-based questions: {image_count}")
        except Exception as e:
            print(f"Error saving Excel file: {e}")
    
    def save_to_csv(self, output_file='questions_output.csv', question_type=None):
        """Save questions to CSV file
        
        Args:
            output_file (str): Output filename
            question_type (str): Filter by type ('text', 'image', or None for all)
        """
        if not self.questions:
            print("No questions found to save!")
            return
        
        # Filter questions by type if specified
        if question_type:
            filtered_questions = [q for q in self.questions if q['question_type'] == question_type]
            if not filtered_questions:
                print(f"No {question_type}-based questions found!")
                return
        else:
            filtered_questions = self.questions
        
        # Define column order
        column_order = ['question_no', 'question_type', 'question_statement', 
                       'option_A', 'option_B', 'option_C', 'option_D', 
                       'correct_answer', 'explanation', 'reference']
        
        try:
            # Save to CSV with UTF-8 encoding
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=column_order, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                
                for question in filtered_questions:
                    # Create ordered dict for writing
                    row = {col: question.get(col, '') for col in column_order}
                    writer.writerow(row)
            
            # Print summary
            text_count = sum(1 for q in filtered_questions if q['question_type'] == 'text')
            image_count = sum(1 for q in filtered_questions if q['question_type'] == 'image')
            
            print(f"[OK] Successfully saved {len(filtered_questions)} questions to {output_file}")
            if not question_type:
                print(f"  - Text-based questions: {text_count}")
                print(f"  - Image-based questions: {image_count}")
        except Exception as e:
            print(f"Error saving CSV file: {e}")
    
    def save_to_json(self, output_file='questions_output.json', pretty=True, question_type=None):
        """Save questions to JSON file
        
        Args:
            output_file (str): Output filename
            pretty (bool): Whether to use pretty formatting
            question_type (str): Filter by type ('text', 'image', or None for all)
        """
        if not self.questions:
            print("No questions found to save!")
            return
        
        # Filter questions by type if specified
        if question_type:
            filtered_questions = [q for q in self.questions if q['question_type'] == question_type]
            if not filtered_questions:
                print(f"No {question_type}-based questions found!")
                return
        else:
            filtered_questions = self.questions
        
        # Structure the JSON with question options as an array
        json_data = {
            "metadata": {
                "total_questions": len(filtered_questions),
                "text_based": sum(1 for q in filtered_questions if q['question_type'] == 'text'),
                "image_based": sum(1 for q in filtered_questions if q['question_type'] == 'image'),
                "filter": question_type if question_type else "all",
                "extracted_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "questions": []
        }
        
        # Format each question
        for q in filtered_questions:
            question_entry = {
                "question_no": q['question_no'],
                "question_type": q['question_type'],
                "question_statement": q['question_statement'],
                "options": [
                    {"key": "A", "text": q['option_A']},
                    {"key": "B", "text": q['option_B']},
                    {"key": "C", "text": q['option_C']},
                    {"key": "D", "text": q['option_D']}
                ],
                "correct_answer": q['correct_answer'],
                "explanation": q['explanation'],
                "reference": q.get('reference', '')
            }
            json_data["questions"].append(question_entry)
        
        try:
            # Save to JSON file with UTF-8 encoding
            with open(output_file, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(json_data, f, ensure_ascii=False)
            
            print(f"[OK] Successfully saved JSON to {output_file}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")
    
    def save_to_pdf(self, output_file='questions_output.pdf', question_type=None):
        """Save questions to PDF file with formatted JSON-like structure
        
        Args:
            output_file (str): Output filename
            question_type (str): Filter by type ('text', 'image', or None for all)
        """
        if not REPORTLAB_AVAILABLE:
            print("Error: reportlab library not available. Install it with: pip install reportlab")
            return
        
        if not self.questions:
            print("No questions found to save!")
            return
        
        # Filter questions by type if specified
        if question_type:
            filtered_questions = [q for q in self.questions if q['question_type'] == question_type]
            if not filtered_questions:
                print(f"No {question_type}-based questions found!")
                return
        else:
            filtered_questions = self.questions
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(output_file, pagesize=letter,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=18)
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#2c5282'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            question_style = ParagraphStyle(
                'QuestionStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#2d3748'),
                spaceAfter=8,
                leading=14
            )
            
            option_style = ParagraphStyle(
                'OptionStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#4a5568'),
                leftIndent=20,
                spaceAfter=6,
                leading=12
            )
            
            answer_style = ParagraphStyle(
                'AnswerStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#38a169'),
                spaceAfter=8,
                leading=12
            )
            
            explanation_style = ParagraphStyle(
                'ExplanationStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#4a5568'),
                spaceAfter=8,
                leading=12
            )
            
            reference_style = ParagraphStyle(
                'ReferenceStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#718096'),
                spaceAfter=8,
                leading=10,
                fontName='Helvetica-Oblique'
            )
            
            # Add title
            title = Paragraph("Extracted Questions", title_style)
            elements.append(title)
            
            # Add metadata
            text_count = sum(1 for q in filtered_questions if q['question_type'] == 'text')
            image_count = sum(1 for q in filtered_questions if q['question_type'] == 'image')
            
            metadata_text = f"Total Questions: {len(filtered_questions)} | Text: {text_count} | Image: {image_count}"
            metadata = Paragraph(metadata_text, question_style)
            elements.append(metadata)
            elements.append(Spacer(1, 0.3*inch))
            
            # Add each question
            for i, q in enumerate(filtered_questions, 1):
                # Question number and type
                q_header = f"<b>Question {q['question_no']}</b> [{q['question_type'].upper()}]"
                elements.append(Paragraph(q_header, heading_style))
                
                # Question statement
                q_text = self._escape_html(q['question_statement'])
                elements.append(Paragraph(f"<b>Q:</b> {q_text}", question_style))
                elements.append(Spacer(1, 0.1*inch))
                
                # Options
                for option_key in ['A', 'B', 'C', 'D']:
                    option_text = self._escape_html(q[f'option_{option_key}'])
                    is_correct = q['correct_answer'] == option_key
                    
                    if is_correct:
                        option_para = f"<b>{option_key}. {option_text} ✓</b>"
                        elements.append(Paragraph(option_para, answer_style))
                    else:
                        option_para = f"{option_key}. {option_text}"
                        elements.append(Paragraph(option_para, option_style))
                
                elements.append(Spacer(1, 0.1*inch))
                
                # Correct answer
                answer_text = f"<b>Answer: {q['correct_answer']}</b>"
                elements.append(Paragraph(answer_text, answer_style))
                
                # Explanation
                if q['explanation']:
                    exp_text = self._escape_html(q['explanation'])
                    elements.append(Paragraph(f"<b>Explanation:</b> {exp_text}", explanation_style))
                
                # Reference
                if q.get('reference'):
                    ref_text = self._escape_html(q['reference'])
                    elements.append(Paragraph(f"<b>Reference:</b> {ref_text}", reference_style))
                
                # Add separator
                if i < len(filtered_questions):
                    elements.append(Spacer(1, 0.2*inch))
                    # Add horizontal line
                    elements.append(Table([['']], colWidths=[6.5*inch], 
                                        style=[('LINEBELOW', (0,0), (-1,-1), 1, colors.grey)]))
                    elements.append(Spacer(1, 0.2*inch))
            
            # Build PDF
            doc.build(elements)
            
            print(f"[OK] Successfully saved {len(filtered_questions)} questions to {output_file}")
            if not question_type:
                print(f"  - Text-based questions: {text_count}")
                print(f"  - Image-based questions: {image_count}")
                
        except Exception as e:
            print(f"Error saving PDF file: {e}")
            import traceback
            traceback.print_exc()
    
    def _escape_html(self, text):
        """Escape HTML special characters for ReportLab
        
        Args:
            text (str): Text to escape
            
        Returns:
            str: Escaped text
        """
        if not text:
            return ""
        
        # Replace special characters
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        return text
        """Save questions to specified format(s)
        
        Args:
            output_file (str): Base output filename (without extension)
            formats (list): List of formats to save ['json', 'excel', 'csv']
            question_type (str): Filter by type ('text', 'image', or None for all)
        """
        if not self.questions:
            print("No questions found to save!")
            return
        
        # Validate formats
        invalid_formats = [fmt for fmt in formats if fmt not in self.SUPPORTED_FORMATS]
        if invalid_formats:
            print(f"Warning: Invalid format(s) {invalid_formats}. Supported: {self.SUPPORTED_FORMATS}")
            formats = [fmt for fmt in formats if fmt in self.SUPPORTED_FORMATS]
        
        if not formats:
            print("No valid formats specified. Using default: json")
            formats = ['json']
        
        # Remove extension from output_file if present
        base_name = os.path.splitext(output_file)[0]
        
        # Save in each requested format
        saved_files = []
        for fmt in formats:
            if fmt == 'json':
                file_path = f"{base_name}.json"
                self.save_to_json(file_path, pretty=True, question_type=question_type)
                saved_files.append(file_path)
            elif fmt == 'excel':
                file_path = f"{base_name}.xlsx"
                self.save_to_excel(file_path, question_type=question_type)
                saved_files.append(file_path)
            elif fmt == 'csv':
                file_path = f"{base_name}.csv"
                self.save_to_csv(file_path, question_type=question_type)
                saved_files.append(file_path)
        
        return saved_files
    
    def save_all(self, base_filename='questions_output', formats=['json'], separate_by_type=True):
        """Save to specified formats with optional separation by type
        
        Args:
            base_filename (str): Base name for output files
            formats (list): List of formats ['json', 'excel', 'csv']
            separate_by_type (bool): If True, creates separate files for text and image questions
        """
        print("\n" + "="*50)
        print("SAVING OUTPUT FILES")
        print("="*50)
        print(f"Formats: {', '.join(formats)}")
        print("="*50)
        
        if separate_by_type:
            # Save all questions combined
            print("\nSaving combined files:")
            self.save(f"{base_filename}_all", formats=formats)
            
            # Save text-based questions separately
            print("\nSaving text-based questions:")
            self.save(f"{base_filename}_text", formats=formats, question_type='text')
            
            # Save image-based questions separately
            print("\nSaving image-based questions:")
            self.save(f"{base_filename}_image", formats=formats, question_type='image')
            
        else:
            # Save all questions in single files
            self.save(base_filename, formats=formats)
        
        print("="*50)
        print("All files saved successfully!")
        print("="*50 + "\n")
    
    def process(self, use_ocr=False):
        """Main processing method
        
        Args:
            use_ocr (bool): Whether to use OCR for image-based PDFs
            
        Returns:
            list: List of extracted questions
        """
        print("Extracting text from PDF...")
        text = self.extract_text_from_pdf()
        
        print(f"Extracted {len(text)} characters from PDF")
        
        # If text extraction is poor or use_ocr is True, try OCR
        if use_ocr and (PDF2IMAGE_AVAILABLE and PYTESSERACT_AVAILABLE):
            print("Using OCR for better extraction...")
            ocr_text = self.extract_text_from_images()
            text += "\n" + ocr_text
        elif use_ocr:
            print("OCR requested but libraries not available. Install pdf2image and pytesseract.")
        
        if len(text.strip()) < 50:
            print("\nWarning: Very little text extracted!")
            print("This could mean:")
            print("1. The PDF is image-based (use OCR)")
            print("2. The PDF is encrypted")
            print("3. The file path is incorrect")
            print(f"\nFirst 200 characters of extracted text:")
            print(text[:200])
            print("\n")
        
        print("Parsing questions...")
        self.parse_questions(text)
        
        print(f"Found {len(self.questions)} questions")
        
        if len(self.questions) == 0 and len(text) > 100:
            print("\nDebugging: Showing first 500 characters of text:")
            print(text[:500])
            print("\n... (continuing)")
        
        return self.questions
    
    def get_questions(self):
        """Get all extracted questions
        
        Returns:
            list: List of question dictionaries
        """
        return self.questions
    
    def get_questions_by_type(self, question_type):
        """Get questions filtered by type
        
        Args:
            question_type (str): 'text' or 'image'
            
        Returns:
            list: Filtered list of questions
        """
        return [q for q in self.questions if q['question_type'] == question_type]
    
    def get_summary(self):
        """Get summary statistics
        
        Returns:
            dict: Summary with counts by type
        """
        return {
            'total': len(self.questions),
            'text_based': len([q for q in self.questions if q['question_type'] == 'text']),
            'image_based': len([q for q in self.questions if q['question_type'] == 'image'])
        }

    

    def save(self, output_file, formats=['json'], question_type=None):
        """Save questions to specified format(s)
        
        Args:
            output_file (str): Base output filename (without extension)
            formats (list): List of formats to save ['json', 'excel', 'csv']
            question_type (str): Filter by type ('text', 'image', or None for all)
        """
        if not self.questions:
            print("No questions found to save!")
            return
        
        # Validate formats
        invalid_formats = [fmt for fmt in formats if fmt not in self.SUPPORTED_FORMATS]
        if invalid_formats:
            print(f"Warning: Invalid format(s) {invalid_formats}. Supported: {self.SUPPORTED_FORMATS}")
            formats = [fmt for fmt in formats if fmt in self.SUPPORTED_FORMATS]
        
        if not formats:
            print("No valid formats specified. Using default: json")
            formats = ['json']
        
        # Remove extension from output_file if present
        base_name = os.path.splitext(output_file)[0]
        
        # Save in each requested format
        saved_files = []
        for fmt in formats:
            if fmt == 'json':
                file_path = f"{base_name}.json"
                self.save_to_json(file_path, pretty=True, question_type=question_type)
                saved_files.append(file_path)
            elif fmt == 'excel':
                file_path = f"{base_name}.xlsx"
                self.save_to_excel(file_path, question_type=question_type)
                saved_files.append(file_path)
            elif fmt == 'csv':
                file_path = f"{base_name}.csv"
                self.save_to_csv(file_path, question_type=question_type)
                saved_files.append(file_path)
        
        return saved_files
    
   
    

 
    