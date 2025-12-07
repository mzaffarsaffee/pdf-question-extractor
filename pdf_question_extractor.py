"""
PDF Question Extractor Library
A library for extracting multiple choice questions from PDF files
and saving them to Excel and JSON formats.
"""

import PyPDF2
import pandas as pd
import re
import os
import json

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


class PDFQuestionExtractor:
    """Extract multiple choice questions from PDF files"""
    
    def __init__(self, pdf_path):
        """Initialize the extractor with a PDF file path
        
        Args:
            pdf_path (str): Path to the PDF file to process
        """
        self.pdf_path = pdf_path
        self.questions = []
    
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
            
            # Detect question type
            all_options = f"{option_a} {option_b} {option_c} {option_d}"
            question_type = self.detect_question_type(question_statement, all_options)
            
            return {
                'question_no': question_no,
                'question_type': question_type,
                'question_statement': question_statement,
                'option_A': option_a,
                'option_B': option_b,
                'option_C': option_c,
                'option_D': option_d,
                'correct_answer': correct_answer,
                'explanation': explanation
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
        
        # Reorder columns with question_type as second column
        column_order = ['question_no', 'question_type', 'question_statement', 
                       'option_A', 'option_B', 'option_C', 'option_D', 
                       'correct_answer', 'explanation']
        df = df[column_order]
        
        # Save to Excel
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        # Print summary
        text_count = len(df[df['question_type'] == 'text'])
        image_count = len(df[df['question_type'] == 'image'])
        
        print(f"[OK] Successfully saved {len(filtered_questions)} questions to {output_file}")
        if not question_type:
            print(f"  - Text-based questions: {text_count}")
            print(f"  - Image-based questions: {image_count}")
    
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
                "filter": question_type if question_type else "all"
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
                "explanation": q['explanation']
            }
            json_data["questions"].append(question_entry)
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(json_data, f, ensure_ascii=False)
        
        print(f"[OK] Successfully saved JSON to {output_file}")
    
    def save_all(self, base_filename='questions_output', separate_by_type=True):
        """Save to both Excel and JSON formats
        
        Args:
            base_filename (str): Base name for output files
            separate_by_type (bool): If True, creates separate files for text and image questions
        """
        print("\n" + "="*50)
        print("SAVING OUTPUT FILES")
        print("="*50)
        
        if separate_by_type:
            # Save all questions combined
            print("\nSaving combined files:")
            excel_all = f"{base_filename}_all.xlsx"
            json_all = f"{base_filename}_all.json"
            self.save_to_excel(excel_all)
            self.save_to_json(json_all)
            
            # Save text-based questions separately
            print("\nSaving text-based questions:")
            excel_text = f"{base_filename}_text.xlsx"
            json_text = f"{base_filename}_text.json"
            self.save_to_excel(excel_text, question_type='text')
            self.save_to_json(json_text, question_type='text')
            
            # Save image-based questions separately
            print("\nSaving image-based questions:")
            excel_image = f"{base_filename}_image.xlsx"
            json_image = f"{base_filename}_image.json"
            self.save_to_excel(excel_image, question_type='image')
            self.save_to_json(json_image, question_type='image')
            
        else:
            # Save all questions in single files
            excel_file = f"{base_filename}.xlsx"
            json_file = f"{base_filename}.json"
            self.save_to_excel(excel_file)
            self.save_to_json(json_file)
        
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