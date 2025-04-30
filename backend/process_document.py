import os
import sys
import time
from API_services.cloud_convert import convert_to_pdf_and_extract_text, process_file_for_gpt
from API_services.gpt import GPT_Process_PDFs

def process_document(file_path):
    """Process a document and save the results to an HTML file"""
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    filename = os.path.basename(file_path)
    print(f"Processing file: {filename}")
    
    try:
        start_time = time.time()
        
        # Step 1: Convert to PDF and extract text
        print("Converting file to PDF and extracting text...")
        with open(file_path, 'rb') as file:
            # Pass the file object and the filename separately
            results = process_file_for_gpt(file, GPT_Process_PDFs, filename)
        
        end_time = time.time()
        
        if results and len(results) > 0:
            result = results[0]
            
            # Save the HTML output to a file
            output_filename = f"{os.path.splitext(filename)[0]}_highlighted.html"
            
            with open(output_filename, "w") as f:
                f.write(result["marked_content"])
            
            print(f"Created HTML file with highlighted content: {output_filename}")
            print(f"Total processing time: {end_time - start_time:.2f} seconds")
            
            # Print highlighting statistics
            if "marked_content" in result:
                html_output = result["marked_content"]
                low_count = html_output.count('<mark class="low">')
                medium_count = html_output.count('<mark class="medium">')
                high_count = html_output.count('<mark class="high">')
                
                print(f"\nHighlighting statistics:")
                print(f"  - Low sensitivity: {low_count} marks")
                print(f"  - Medium sensitivity: {medium_count} marks")
                print(f"  - High sensitivity: {high_count} marks")
                print(f"  - Total highlights: {low_count + medium_count + high_count}")
        else:
            print("No results returned from processing")
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Add the parent directory to the path so we can import the API_services module
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    if len(sys.argv) < 2:
        print("Usage: python process_document.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    process_document(file_path) 