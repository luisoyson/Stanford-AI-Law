import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS

# Create a simple Flask app for testing
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Test HTML with different highlight levels
TEST_HTML = """<!DOCTYPE html>
<html>
<head>
<style>
    mark.low { background-color: yellow; }
    mark.medium { background-color: orange; }
    mark.high { background-color: red; }
    body { 
        font-family: Arial, sans-serif; 
        line-height: 1.6;
        margin: 20px;
    }
</style>
</head>
<body>
<h1>Test Document with Different Highlight Levels</h1>

<p><mark class="low">This is a LOW sensitivity sentence that should be highlighted in yellow.</mark></p>
<p><mark class="medium">This is a MEDIUM sensitivity sentence that should be highlighted in orange.</mark></p>
<p><mark class="high">This is a HIGH sensitivity sentence that should be highlighted in red.</mark></p>

<p>This is a normal sentence with no highlighting.</p>

<p>This paragraph contains <mark class="low">low</mark>, <mark class="medium">medium</mark>, and <mark class="high">high</mark> sensitivity terms.</p>

<p><mark class="low">The first part of this sentence is low sensitivity,</mark> <mark class="medium">the middle part is medium sensitivity,</mark> <mark class="high">and the last part is high sensitivity.</mark></p>
</body>
</html>"""

@app.route('/api/process-documents', methods=['POST', 'OPTIONS'])
def process_documents():
    """Serve a test response with different highlight levels"""
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        return '', 204
    
    print("Received request to process documents")
    
    # Create a test response
    result = {
        "filename": "test_document.txt",
        "document_index": 0,
        "marked_content": TEST_HTML,
        "pdf_url": None
    }
    
    # Log highlight counts for debugging
    low_count = TEST_HTML.count('<mark class="low">')
    medium_count = TEST_HTML.count('<mark class="medium">')
    high_count = TEST_HTML.count('<mark class="high">')
    
    print(f"Highlight statistics:")
    print(f"  - Low sensitivity: {low_count} marks")
    print(f"  - Medium sensitivity: {medium_count} marks")
    print(f"  - High sensitivity: {high_count} marks")
    print(f"  - Total highlights: {low_count + medium_count + high_count}")
    
    return jsonify([result])

@app.after_request
def after_request(response):
    """Add CORS headers to every response"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    print("Starting test server on port 5001")
    print("This server will return HTML with different highlight colors")
    print("Use the Swift app to connect to this server and test the rendering")
    app.run(debug=True, port=5001, host='0.0.0.0') 