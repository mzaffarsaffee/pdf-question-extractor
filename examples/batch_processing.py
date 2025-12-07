"""
Example: Batch Processing Multiple PDFs
This script demonstrates how to process multiple PDF files at once
"""

import sys
import os

# Add parent directory to path to import the library
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pdf_question_extractor import PDFQuestionExtractor


def batch_process_pdfs(pdf_files, output_dir="batch_output", use_ocr=False):
    """
    Process multiple PDF files and save results
    
    Args:
        pdf_files (list): List of PDF file paths
        output_dir (str): Directory to save output files
        use_ocr (bool): Whether to use OCR
    """
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    results = {
        'successful': [],
        'failed': [],
        'total_questions': 0
    }
    
    print("="*60)
    print("BATCH PROCESSING PDFs")
    print("="*60)
    print(f"Files to process: {len(pdf_files)}")
    print(f"Output directory: {output_dir}")
    print(f"OCR enabled: {use_ocr}")
    print("="*60 + "\n")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file}")
        print("-" * 60)
        
        # Check if file exists
        if not os.path.exists(pdf_file):
            print(f"ERROR: File not found - {pdf_file}")
            results['failed'].append({'file': pdf_file, 'error': 'File not found'})
            continue
        
        try:
            # Initialize extractor
            extractor = PDFQuestionExtractor(pdf_file)
            
            # Process PDF
            questions = extractor.process(use_ocr=use_ocr)
            
            if questions:
                # Create output filename from input filename
                basename = os.path.splitext(os.path.basename(pdf_file))[0]
                output_path = os.path.join(output_dir, basename)
                
                # Save results
                extractor.save_all(output_path, separate_by_type=True)
                
                # Record success
                summary = extractor.get_summary()
                results['successful'].append({
                    'file': pdf_file,
                    'questions': summary['total'],
                    'text': summary['text_based'],
                    'image': summary['image_based']
                })
                results['total_questions'] += summary['total']
                
                print(f"✓ Successfully extracted {summary['total']} questions")
            else:
                print(f"✗ No questions extracted from {pdf_file}")
                results['failed'].append({'file': pdf_file, 'error': 'No questions found'})
                
        except Exception as e:
            print(f"✗ Error processing {pdf_file}: {e}")
            results['failed'].append({'file': pdf_file, 'error': str(e)})
    
    # Print summary
    print("\n" + "="*60)
    print("BATCH PROCESSING SUMMARY")
    print("="*60)
    print(f"Total files processed: {len(pdf_files)}")
    print(f"Successful: {len(results['successful'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Total questions extracted: {results['total_questions']}")
    
    if results['successful']:
        print("\n✓ Successfully processed files:")
        for item in results['successful']:
            print(f"  - {item['file']}: {item['questions']} questions "
                  f"({item['text']} text, {item['image']} image)")
    
    if results['failed']:
        print("\n✗ Failed files:")
        for item in results['failed']:
            print(f"  - {item['file']}: {item['error']}")
    
    print("="*60 + "\n")
    
    return results


def main():
    """Example usage"""
    
    # Example 1: Process specific files
    pdf_files = [
        "chapter1.pdf",
        "chapter2.pdf",
        "chapter3.pdf"
    ]
    
    # Example 2: Process all PDFs in a directory
    # pdf_directory = "pdfs"
    # pdf_files = [os.path.join(pdf_directory, f) for f in os.listdir(pdf_directory) 
    #              if f.endswith('.pdf')]
    
    # Process the files
    results = batch_process_pdfs(
        pdf_files=pdf_files,
        output_dir="batch_output",
        use_ocr=False
    )
    
    # You can also access individual results
    if results['successful']:
        print(f"\nFirst successful file had {results['successful'][0]['questions']} questions")


if __name__ == "__main__":
    main()