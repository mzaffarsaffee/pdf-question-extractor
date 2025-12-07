"""
Main script to run the PDF Question Extractor
Configure your settings here and run this file
"""

from pdf_question_extractor import PDFQuestionExtractor
import os


def main():
    """Main function to configure and run the extractor"""
    
    # ============================================
    # CONFIGURATION - EDIT THESE SETTINGS
    # ============================================
    
    # Input PDF file path
    pdf_file = "input/azure-ai-102-001.pdf"  # Change this to your PDF file path
    
    # Output settings
    output_directory = "azure-ai-102-001"  # Directory to save output files
    output_base_name = "azure-ai-102-001"  # Base name for output files
    
    # Output formats - Choose one or more: 'json', 'excel', 'csv', 'pdf'
    # Default is 'json' only
    output_formats = ['json', 'pdf']  # Options: ['json'], ['excel'], ['csv'], ['pdf'], or ['json', 'excel', 'csv', 'pdf']
    
    # Processing options
    use_ocr = True  # Set to True if PDF contains image-based questions
    separate_by_type = True  # Set to True to create separate files for text/image questions
    
    # Display options
    show_sample = True  # Show a sample question after extraction
    show_summary = True  # Show summary statistics
    
    # ============================================
    # EXAMPLE CONFIGURATIONS:
    # ============================================
    # 
    # Config 1: JSON only (default)
    # output_formats = ['json']
    #
    # Config 2: Excel only
    # output_formats = ['excel']
    #
    # Config 3: CSV only
    # output_formats = ['csv']
    #
    # Config 4: PDF only (formatted document)
    # output_formats = ['pdf']
    #
    # Config 5: All formats
    # output_formats = ['json', 'excel', 'csv', 'pdf']
    #
    # Config 6: JSON + PDF (best for review)
    # output_formats = ['json', 'pdf']
    #
    # ============================================
    # END CONFIGURATION
    # ============================================
    
    # Validate output formats
    supported_formats = ['json', 'excel', 'csv', 'pdf']
    invalid_formats = [fmt for fmt in output_formats if fmt not in supported_formats]
    if invalid_formats:
        print(f"Warning: Invalid format(s) {invalid_formats}")
        print(f"Supported formats: {supported_formats}")
        output_formats = [fmt for fmt in output_formats if fmt in supported_formats]
    
    if not output_formats:
        print("No valid formats specified. Using default: json")
        output_formats = ['json']
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created output directory: {output_directory}")
    
    # Validate input file
    if not os.path.exists(pdf_file):
        print(f"Error: PDF file not found: {pdf_file}")
        print("Please check the file path and try again.")
        return
    
    print("\n" + "="*60)
    print("PDF QUESTION EXTRACTOR")
    print("="*60)
    print(f"Input file: {pdf_file}")
    print(f"Output directory: {output_directory}")
    print(f"Output formats: {', '.join(output_formats)}")
    print(f"OCR enabled: {use_ocr}")
    print(f"Separate by type: {separate_by_type}")
    print("="*60 + "\n")
    
    # Initialize the extractor
    extractor = PDFQuestionExtractor(pdf_file)
    
    # Process the PDF
    questions = extractor.process(use_ocr=use_ocr)
    
    # Check if questions were extracted
    if not questions:
        print("\n" + "="*60)
        print("ERROR: No questions were extracted!")
        print("="*60)
        print("\nPossible solutions:")
        print("1. If PDF is image-based, set use_ocr=True")
        print("2. Check if PDF format matches expected structure")
        print("3. Try opening the PDF manually to verify it's readable")
        print("4. Check the debug output above for more details")
        return
    
    # Build output path
    output_path = os.path.join(output_directory, output_base_name)
    
    # Save the extracted questions in specified formats
    extractor.save_all(output_path, formats=output_formats, separate_by_type=separate_by_type)
    
    # Display summary
    if show_summary:
        summary = extractor.get_summary()
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        print(f"Total questions extracted: {summary['total']}")
        print(f"Text-based questions: {summary['text_based']}")
        print(f"Image-based questions: {summary['image_based']}")
        print("="*60)
    
    # Display sample question
    if show_sample and questions:
        print("\n" + "="*60)
        print("SAMPLE QUESTION")
        print("="*60)
        sample = questions[0]
        print(f"Question No: {sample['question_no']}")
        print(f"Type: {sample['question_type']}")
        print(f"\nStatement:")
        statement = sample['question_statement']
        print(statement[:200] + "..." if len(statement) > 200 else statement)
        
        option_a = sample['option_A']
        option_b = sample['option_B']
        print(f"\nOption A: {option_a[:100]}..." if len(option_a) > 100 else f"\nOption A: {option_a}")
        print(f"Option B: {option_b[:100]}..." if len(option_b) > 100 else f"Option B: {option_b}")
        print(f"\nCorrect Answer: {sample['correct_answer']}")
        print("="*60 + "\n")
    
    # List output files
    print("\nOutput files created:")
    
    # Determine file extensions based on formats
    extensions = []
    if 'json' in output_formats:
        extensions.append('.json')
    if 'excel' in output_formats:
        extensions.append('.xlsx')
    if 'csv' in output_formats:
        extensions.append('.csv')
    if 'pdf' in output_formats:
        extensions.append('.pdf')
    
    # List files based on separation setting
    if separate_by_type:
        suffixes = ['_all', '_text', '_image']
    else:
        suffixes = ['']
    
    for suffix in suffixes:
        for ext in extensions:
            filename = f"{output_base_name}{suffix}{ext}"
            filepath = os.path.join(output_directory, filename)
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"  - {filepath} ({file_size:,} bytes)")
    
    print("\n" + "="*60)
    print("EXTRACTION COMPLETED SUCCESSFULLY!")
    print("="*60 + "\n")
    
    # Show format-specific notes
    print("Format Notes:")
    if 'json' in output_formats:
        print("  - JSON: Best for APIs and web applications")
    if 'excel' in output_formats:
        print("  - Excel: Best for manual review and editing")
    if 'csv' in output_formats:
        print("  - CSV: Best for database imports and data analysis")
    if 'pdf' in output_formats:
        print("  - PDF: Best for printing and professional presentation")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()