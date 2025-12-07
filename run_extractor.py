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
    pdf_file = "comptia-sy0-701-001.pdf"  # Change this to your PDF file path
    
    # Output settings
    output_directory = "output"  # Directory to save output files
    output_base_name = "comptia-sy0-701-001"  # Base name for output files
    
    # Processing options
    use_ocr = True  # Set to True if PDF contains image-based questions
    separate_by_type = True  # Set to True to create separate files for text/image questions
    
    # Display options
    show_sample = True  # Show a sample question after extraction
    show_summary = True  # Show summary statistics
    
    # ============================================
    # END CONFIGURATION
    # ============================================
    
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
    
    # Save the extracted questions
    extractor.save_all(output_path, separate_by_type=separate_by_type)
    
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
        print(sample['question_statement'][:200] + "..." if len(sample['question_statement']) > 200 else sample['question_statement'])
        print(f"\nOption A: {sample['option_A'][:100]}..." if len(sample['option_A']) > 100 else f"\nOption A: {sample['option_A']}")
        print(f"Option B: {sample['option_B'][:100]}..." if len(sample['option_B']) > 100 else f"Option B: {sample['option_B']}")
        print(f"\nCorrect Answer: {sample['correct_answer']}")
        print("="*60 + "\n")
    
    # List output files
    print("\nOutput files created:")
    if separate_by_type:
        files = [
            f"{output_base_name}_all.xlsx",
            f"{output_base_name}_all.json",
            f"{output_base_name}_text.xlsx",
            f"{output_base_name}_text.json",
            f"{output_base_name}_image.xlsx",
            f"{output_base_name}_image.json"
        ]
    else:
        files = [
            f"{output_base_name}.xlsx",
            f"{output_base_name}.json"
        ]
    
    for filename in files:
        filepath = os.path.join(output_directory, filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"  - {filepath} ({file_size:,} bytes)")
    
    print("\n" + "="*60)
    print("EXTRACTION COMPLETED SUCCESSFULLY!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()