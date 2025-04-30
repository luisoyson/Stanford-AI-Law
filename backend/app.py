import os
import json
import uuid
import logging
from flask_cors import CORS
from flask import Flask, request, jsonify, send_from_directory, render_template, url_for
import PyPDF2

from API_services.gpt import GPT_Process_PDFs
from API_services.cloud_convert import process_file_for_gpt

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, 
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

# Enable CORS for all routes and all domains
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Create a directory to store uploaded PDFs
UPLOAD_FOLDER = os.path.join('..', 'frontend', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text(pdf_file):
    """Extract text from a PDF file"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

@app.route('/')
def index():
    """Serve the frontend interface"""
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    if filename.endswith('.pdf'):
        logger.info(f"Serving PDF file: {filename}")
        response = send_from_directory(UPLOAD_FOLDER, filename, mimetype='application/pdf')
        # Add headers to help with caching and display
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        response.headers['Cache-Control'] = 'no-cache'
        return response
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/process-documents', methods=['POST', 'OPTIONS'])
def process_documents():
    """Process documents using CloudConvert and GPT"""
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        return '', 204
    
    # Log the request details
    logger.info(f"Received request to process documents")
    logger.debug(f"Request headers: {request.headers}")
    logger.debug(f"Request form data: {request.form}")
    logger.debug(f"Request files: {list(request.files.keys())}")
    
    # Get files from request - handle both 'files' and 'file' keys
    files = []
    if 'files' in request.files:
        files = request.files.getlist('files')
        logger.info(f"Found {len(files)} files under 'files' key")
    elif 'file' in request.files:
        files = [request.files['file']]
        logger.info(f"Found 1 file under 'file' key")
    
    # Error handling
    if not files or all(not file.filename for file in files):
        logger.error("No files provided in request")
        return jsonify({'error': 'No files provided'}), 400
    
    # Get optional context from the form
    context = request.form.get('context', '')
    if context:
        logger.info(f"Received context: {context[:100]}...")
    
    # Log file details
    for file in files:
        logger.info(f"Processing file: {file.filename}, Content-Type: {file.content_type}")
    
    # Process files one at a time
    results = []
    for file in files:
        try:
            # Convert to PDF and process with GPT in one step
            logger.info(f"Starting processing of file: {file.filename}")
            
            # Pass the context if provided
            logger.debug("Converting file to PDF and extracting text")
            file_results = process_file_for_gpt(file, GPT_Process_PDFs, file.filename)
            
            logger.info(f"Processing complete for file: {file.filename}")
            
            # Add results to the list
            if file_results and len(file_results) > 0:
                result = file_results[0]
                
                # If we have a PDF path from the conversion
                if 'pdf_path' in result and os.path.exists(result['pdf_path']):
                    # Create a unique filename for the PDF
                    pdf_filename = f"{uuid.uuid4().hex}.pdf"
                    pdf_destination = os.path.join(UPLOAD_FOLDER, pdf_filename)
                    
                    # Copy the PDF to the static folder
                    logger.info(f"Copying PDF from {result['pdf_path']} to {pdf_destination}")
                    os.rename(result['pdf_path'], pdf_destination)
                    
                    # Add PDF URL to the result
                    pdf_url = url_for('uploaded_file', filename=pdf_filename)
                    result['pdf_url'] = pdf_url
                    logger.info(f"PDF URL added to result: {pdf_url}")
                
                # Add filename if not already present
                if 'filename' not in result:
                    result['filename'] = file.filename
                
                # Log highlighting statistics
                if 'marked_content' in result:
                    html_content = result['marked_content']
                    low_count = html_content.count('<mark class="low">')
                    medium_count = html_content.count('<mark class="medium">')
                    high_count = html_content.count('<mark class="high">')
                    
                    logger.info(f"Highlighting statistics for {file.filename}:")
                    logger.info(f"  - Low sensitivity: {low_count} marks")
                    logger.info(f"  - Medium sensitivity: {medium_count} marks")
                    logger.info(f"  - High sensitivity: {high_count} marks")
                    logger.info(f"  - Total highlights: {low_count + medium_count + high_count}")
                
                results.append(result)
                
        except Exception as e:
            # Log the error but continue processing other files
            logger.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
            # Add error to results
            results.append({
                "filename": file.filename,
                "error": str(e),
                "marked_content": f"<p>Error processing file: {str(e)}</p>"
            })
    
    # Log the response
    logger.info(f"Returning {len(results)} results")
    return jsonify(results)

@app.after_request
def after_request(response):
    """Add CORS headers to every response"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs('../frontend/templates', exist_ok=True)
    os.makedirs('../frontend/static', exist_ok=True)
    
    # Create a basic index.html if it doesn't exist
    if not os.path.exists('../frontend/templates/index.html'):
        with open('../frontend/templates/index.html', 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Document Analysis Tool</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .upload-container { border: 2px dashed #ccc; padding: 20px; text-align: center; }
        .results { margin-top: 20px; }
        .document-container { margin-bottom: 40px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .pdf-viewer { width: 100%; height: 600px; border: 1px solid #ccc; margin-bottom: 20px; }
        .highlighted-text { margin-top: 20px; border: 1px solid #ccc; padding: 10px; }
        mark.low { background-color: yellow; padding: 2px 0; border-radius: 2px; }
        mark.medium { background-color: orange; padding: 2px 0; border-radius: 2px; }
        mark.high { background-color: red; padding: 2px 0; border-radius: 2px; color: white; }
        .legend { margin-top: 10px; font-size: 14px; }
        .legend-item { display: inline-block; margin-right: 20px; }
        .legend-color { display: inline-block; width: 20px; height: 14px; margin-right: 5px; vertical-align: middle; }
        .low-color { background-color: yellow; }
        .medium-color { background-color: orange; }
        .high-color { background-color: red; }
    </style>
</head>
<body>
    <h1>Document Analysis Tool</h1>
    
    <div class="upload-container">
        <h2>Upload Documents</h2>
        <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" id="fileInput" name="files" multiple accept=".pdf,.docx,.xlsx">
            <textarea id="contextInput" placeholder="Optional: Provide additional context about the document..." rows="3" style="width: 100%; margin-top: 10px;"></textarea>
            <button type="submit">Analyze Documents</button>
        </form>
    </div>
    
    <div class="results" id="results"></div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const fileInput = document.getElementById('fileInput');
            const contextInput = document.getElementById('contextInput');
            
            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append('files', fileInput.files[i]);
            }
            
            // Add context if provided
            if (contextInput.value.trim()) {
                formData.append('context', contextInput.value);
            }
            
            document.getElementById('results').innerHTML = '<p>Processing documents... This may take a while.</p>';
            
            try {
                const response = await fetch('/api/process-documents', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                let resultsHTML = '<h2>Analysis Results</h2>';
                
                if (data.length === 0) {
                    resultsHTML += '<p>No results returned.</p>';
                } else {
                    // Add legend
                    resultsHTML += `
                        <div class="legend">
                            <p><strong>Sensitivity Legend:</strong></p>
                            <div class="legend-item"><span class="legend-color low-color"></span> Low Sensitivity</div>
                            <div class="legend-item"><span class="legend-color medium-color"></span> Medium Sensitivity</div>
                            <div class="legend-item"><span class="legend-color high-color"></span> High Sensitivity</div>
                        </div>
                    `;
                    
                    data.forEach(result => {
                        resultsHTML += `<div class="document-container">`;
                        resultsHTML += `<h3>Results for ${result.filename}</h3>`;
                        
                        if (result.error) {
                            resultsHTML += `<p>Error: ${result.error}</p>`;
                        } else {
                            // Display PDF if available
                            if (result.pdf_url) {
                                resultsHTML += `
                                    <h4>Original Document</h4>
                                    <iframe class="pdf-viewer" src="${result.pdf_url}"></iframe>
                                `;
                            }
                            
                            // Count highlights
                            const content = result.marked_content || '';
                            const lowCount = (content.match(/<mark class="low">/g) || []).length;
                            const mediumCount = (content.match(/<mark class="medium">/g) || []).length;
                            const highCount = (content.match(/<mark class="high">/g) || []).length;
                            const totalCount = lowCount + mediumCount + highCount;
                            
                            // Display highlight counts
                            resultsHTML += `
                                <div class="highlight-counts">
                                    <p><strong>Highlight Counts:</strong></p>
                                    <p>Low Sensitivity: ${lowCount} | Medium Sensitivity: ${mediumCount} | High Sensitivity: ${highCount} | Total: ${totalCount}</p>
                                </div>
                            `;
                            
                            // Display highlighted text
                            resultsHTML += `
                                <h4>Document with Highlighted Sensitive Information</h4>
                                <div class="highlighted-text">${result.marked_content}</div>
                            `;
                        }
                        
                        resultsHTML += `</div>`;
                    });
                }
                
                document.getElementById('results').innerHTML = resultsHTML;
                
            } catch (error) {
                document.getElementById('results').innerHTML = `<p>Error: ${error.message}</p>`;
            }
        });
    </script>
</body>
</html>''')
    
    logger.info("Starting Flask server on port 5001")
    app.run(debug=True, port=5001, host='0.0.0.0')
