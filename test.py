import PyPDF2
import pandas as pd

print("PyPDF2 imported")
print("Pandas imported")

try:
    from Crypto.Cipher import AES
    print("PyCryptodome installed")
except:
    print("PyCryptodome NOT installed")

try:
    from pdf2image import convert_from_path
    print("pdf2image installed")
except:
    print("pdf2image NOT installed (OK if not using OCR)")

try:
    import pytesseract
    print("pytesseract installed")
except:
    print("pytesseract NOT installed (OK if not using OCR)")




print("\nSetup check complete!")