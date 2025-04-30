import os
import sys
import requests
import json

def test_api(file_path, api_url="http://127.0.0.1:5001/api/process-documents"):
    """
    Test the API endpoint with a single file
    
    Args:
        file_path: Path to the file to upload
        api_url: URL of the API endpoint
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return
    
    file_name = os.path.basename(file_path)
    print(f"Testing API with file: {file_name}")
    
    # Create a multipart form-data request
    files = {
        'files': (file_name, open(file_path, 'rb'), 'application/pdf')
    }
    
    # Optional context
    data = {
        'context': 'Test context from API test script'
    }
    
    print(f"Sending request to {api_url}")
    try:
        response = requests.post(api_url, files=files, data=data)
        
        # Print response details
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            # Parse the JSON response
            json_response = response.json()
            print(f"Response JSON: {json.dumps(json_response, indent=2)}")
            
            # Check if the response contains the expected fields
            if json_response and len(json_response) > 0:
                result = json_response[0]
                print("\nResult details:")
                print(f"  Filename: {result.get('filename')}")
                print(f"  PDF URL: {result.get('pdf_url')}")
                if 'marked_content' in result:
                    content_preview = result['marked_content'][:100] + "..." if len(result['marked_content']) > 100 else result['marked_content']
                    print(f"  Marked content preview: {content_preview}")
                if 'error' in result:
                    print(f"  Error: {result.get('error')}")
            else:
                print("Empty or invalid response")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception during API test: {str(e)}")
    finally:
        # Close the file
        files['files'][1].close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <file_path> [api_url]")
        print("Example: python test_api.py ./Fox\\ Case/sample.pdf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Optional API URL
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5001/api/process-documents"
    
    test_api(file_path, api_url) 