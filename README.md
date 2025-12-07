![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

PDF Question Extractor
A Python library to extract multiple choice questions from PDF files and save them to Excel and JSON formats. Supports both text-based and image-based PDFs with OCR capabilities.
Features
✅ Extract questions from text-based PDFs
✅ OCR support for scanned/image-based PDFs
✅ Automatic question type detection (text/image)
✅ Export to Excel and JSON formats
✅ Separate files for text and image questions
✅ Handles encrypted PDFs
✅ Well-structured output with metadata
Installation
1. Clone the Repository
bashgit clone https://github.com/mzaffarsaffee/pdf-question-extractor.git
cd pdf-question-extractor
2. Install Dependencies
bashpip install -r requirements.txt
3. Additional Setup for OCR (Optional)
If you need to process image-based PDFs, install these additional tools:
Windows
Poppler:

Download from poppler-windows releases
Extract to C:\poppler
Add C:\poppler\Library\bin to your PATH

Tesseract:

Download from Tesseract releases
Install to default location
Add to PATH or the script will find it automatically

Linux
bashsudo apt-get install poppler-utils tesseract-ocr
macOS
bashbrew install poppler tesseract
Quick Start
Basic Usage

Place your PDF file in the project directory
Edit run_extractor.py:

python   pdf_file = "your_questions.pdf"

Run the script:

bash   python run_extractor.py
Output
The script creates 6 files by default:

extracted_questions_all.xlsx - All questions (Excel)
extracted_questions_all.json - All questions (JSON)
extracted_questions_text.xlsx - Text questions only (Excel)
extracted_questions_text.json - Text questions only (JSON)
extracted_questions_image.xlsx - Image questions only (Excel)
extracted_questions_image.json - Image questions only (JSON)

Configuration
Edit settings in run_extractor.py:
python# Input PDF file path
pdf_file = "your_questions.pdf"

# Output settings
output_directory = "output"
output_base_name = "extracted_questions"

# Processing options
use_ocr = False  # Set to True for image-based PDFs
separate_by_type = True  # Set to False to combine all questions

# Display options
show_sample = True
show_summary = True
Usage as a Library
You can also import and use the extractor in your own scripts:
pythonfrom pdf_question_extractor import PDFQuestionExtractor

# Initialize extractor
extractor = PDFQuestionExtractor("questions.pdf")

# Process PDF
questions = extractor.process(use_ocr=False)

# Save all formats
extractor.save_all("output/questions")

# Get questions by type
text_questions = extractor.get_questions_by_type('text')
image_questions = extractor.get_questions_by_type('image')

# Get summary statistics
summary = extractor.get_summary()
print(f"Total: {summary['total']}")
Expected PDF Format
The extractor expects PDFs with the following structure:
QUESTION NO: 1

[Question statement text here]

A. [Option A text]
B. [Option B text]
C. [Option C text]
D. [Option D text]

ANSWER: C

Explanation:
[Explanation text here]

QUESTION NO: 2
...
Output Structure
Excel Format
question_noquestion_typequestion_statementoption_Aoption_Boption_Coption_Dcorrect_answerexplanation1textA security team...Secure cookiesVersion controlInput validationCode signingCInput validation...
JSON Format
json{
  "metadata": {
    "total_questions": 50,
    "text_based": 45,
    "image_based": 5,
    "filter": "all"
  },
  "questions": [
    {
      "question_no": "1",
      "question_type": "text",
      "question_statement": "A security team is reviewing...",
      "options": [
        {"key": "A", "text": "Secure cookies"},
        {"key": "B", "text": "Version control"},
        {"key": "C", "text": "Input validation"},
        {"key": "D", "text": "Code signing"}
      ],
      "correct_answer": "C",
      "explanation": "Input validation is a technique..."
    }
  ]
}
Advanced Usage
Batch Processing Multiple PDFs
pythonfrom pdf_question_extractor import PDFQuestionExtractor
import os

pdf_files = ["chapter1.pdf", "chapter2.pdf", "chapter3.pdf"]

for pdf_file in pdf_files:
    extractor = PDFQuestionExtractor(pdf_file)
    questions = extractor.process()
    
    if questions:
        basename = os.path.splitext(pdf_file)[0]
        extractor.save_all(f"output/{basename}")
Custom Filtering
python# Save only text questions
extractor.save_to_excel("text_only.xlsx", question_type='text')

# Save only image questions
extractor.save_to_json("image_only.json", question_type='image')
Troubleshooting
No Questions Extracted
Problem: Found 0 questions
Solutions:

Enable OCR: Set use_ocr=True for image-based PDFs
Check PDF format matches expected structure
Review debug output for extracted text sample

OCR Not Working
Problem: Unable to get page count
Solutions:

Ensure poppler is installed and in PATH
Check poppler bin directory path
Install dependencies: pip install pdf2image pytesseract

Encrypted PDF Error
Problem: PyCryptodome is required
Solution:
bashpip install pycryptodome
Unicode/Encoding Errors
The library handles encoding issues automatically. If you still encounter problems, ensure you're using Python 3.7+.
Requirements

Python 3.7+
PyPDF2
pandas
openpyxl
pycryptodome (for encrypted PDFs)
pdf2image (optional, for OCR)
pytesseract (optional, for OCR)
Pillow (optional, for OCR)

Project Structure
pdf-question-extractor/
├── pdf_question_extractor.py   # Main library
├── run_extractor.py             # Runner script
├── requirements.txt             # Dependencies
├── README.md                    # This file
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore rules
├── examples/                    # Example scripts
│   └── batch_processing.py
└── output/                      # Output directory (auto-created)
Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the repository
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

License
This project is licensed under the MIT License - see the LICENSE file for details.
Acknowledgments

Built with PyPDF2 for PDF processing
Uses Tesseract OCR for image text extraction
Powered by pandas for data manipulation

Support
If you encounter any issues or have questions:

Open an issue on GitHub
Check the Troubleshooting section
Review example scripts in the examples/ directory

Changelog
Version 1.0.0 (2024-12-07)

Initial release
Support for text-based PDF extraction
OCR support for image-based PDFs
Excel and JSON export formats
Automatic question type detection
Separate output files by question type


Made with ❤️ for educators and students