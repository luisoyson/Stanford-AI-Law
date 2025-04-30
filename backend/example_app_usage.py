"""
Example of how app.py could use the enhanced cloud_convert.py functionality
This file is for demonstration only and doesn't modify the actual app.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from API_services.gpt import GPT_Process_PDFs
from API_services.cloud_convert import process_file_for_gpt, process_files_batch

app = Flask(__name__)
CORS(app)

@app.route('/api/process-documents', methods=['POST'])
def process_documents():
    """
    Example implementation of process_documents using the enhanced cloud_convert.py
    This handles all file formats by converting them to PDF first, then processing with GPT
    """
    # Get files from request
    files = request.files.getlist('files')
    
    # Error handling
    if not files or all(not file.filename for file in files):
        return jsonify({'error': 'No files provided'}), 400
    
    results = []
    
    # Option 1: Process each file individually
    for file in files:
        try:
            # Convert to PDF and process with GPT in one step
            file_results = process_file_for_gpt(file, GPT_Process_PDFs)
            
            # Add results to the list
            if file_results and len(file_results) > 0:
                results.append(file_results[0])
                
        except Exception as e:
            # Log the error but continue processing other files
            print(f"Error processing file {file.filename}: {str(e)}")
    
    # Option 2: Process all files in batch
    # results = process_files_batch(files, GPT_Process_PDFs)
    
    return jsonify(results)

if __name__ == '__main__':
    print("This is just an example file showing how app.py could use the enhanced cloud_convert.py")
    print("To test the actual functionality, run:")
    print("  python example_usage.py <file_path_or_directory>")
    # app.run(debug=True, port=5001) 