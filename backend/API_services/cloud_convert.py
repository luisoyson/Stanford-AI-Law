import os
import tempfile
import cloudconvert
from dotenv import load_dotenv
import PyPDF2
import io

# Get absolute path to the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(backend_dir)

# Load environment variables from the root .env file
load_dotenv(os.path.join(root_dir, ".env"))

def initialize_cloud_convert():
    """
    Initialize the CloudConvert API client using API key from environment variable
    """
    api_key = os.getenv('CLOUDCONVERT_API_KEY')
    if not api_key:
        raise ValueError("CLOUDCONVERT_API_KEY environment variable not set")
    
    # Configure the CloudConvert client
    cloudconvert.configure(api_key=api_key, sandbox=False)

def convert_file(input_file_path, output_format):
    """
    Convert a file to the specified format using CloudConvert API
    
    Args:
        input_file_path (str): Path to the input file
        output_format (str): Desired output format (e.g., 'pdf', 'docx', 'xlsx')
        
    Returns:
        dict: Information about the converted file including download URL
    """
    initialize_cloud_convert()
    
    # Extract filename from path
    filename = os.path.basename(input_file_path)
    
    # Create a job with upload task
    job = cloudconvert.Job.create(payload={
        'tasks': {
            'upload-file': {
                'operation': 'import/upload'
            },
            'convert-file': {
                'operation': 'convert',
                'input': 'upload-file',
                'output_format': output_format
            },
            'export-file': {
                'operation': 'export/url',
                'input': 'convert-file'
            }
        }
    })
    
    # Find the upload task ID
    upload_task_id = None
    for task in job['tasks']:
        if task['operation'] == 'import/upload':
            upload_task_id = task['id']
            break
    
    if not upload_task_id:
        raise Exception("Upload task not found in the job")
    
    # Get the upload task
    upload_task = cloudconvert.Task.find(id=upload_task_id)
    
    # Upload the file
    cloudconvert.Task.upload(file_name=input_file_path, task=upload_task)
    
    # Wait for the job to finish
    job_id = job['id']
    job_info = cloudconvert.Job.wait(id=job_id)
    
    # Get the export task to find the download URL
    export_task = None
    for task in job_info['tasks']:
        if task['operation'] == 'export/url':
            export_task = task
            break
    
    if not export_task or export_task['status'] != 'finished':
        raise Exception("Export task failed or not found")
    
    # Return the file info including download URL
    return export_task['result']['files'][0]

def convert_and_download(input_file_path, output_format, output_file_path=None):
    """
    Convert a file and download the result
    
    Args:
        input_file_path (str): Path to the input file
        output_format (str): Desired output format (e.g., 'pdf', 'docx', 'xlsx')
        output_file_path (str, optional): Path where to save the output file. 
                                         If not provided, will use the input filename with new extension.
    
    Returns:
        str: Path to the downloaded file
    """
    # Convert the file
    file_info = convert_file(input_file_path, output_format)
    
    # Determine output filename if not provided
    if not output_file_path:
        input_basename = os.path.splitext(os.path.basename(input_file_path))[0]
        output_file_path = f"{input_basename}.{output_format}"
    
    # Download the file
    cloudconvert.download(url=file_info['url'], filename=output_file_path)
    
    return output_file_path

def extract_text_from_pdf(pdf_file):
    """
    Extract text from a PDF file
    
    Args:
        pdf_file: File object or path to PDF file
        
    Returns:
        str: Extracted text
    """
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def convert_to_pdf_and_extract_text(file_object, filename=None):
    """
    Convert any file to PDF and extract text
    
    Args:
        file_object: File object from request.files or a file path
        filename (str, optional): Name of the file if file_object doesn't have it
        
    Returns:
        tuple: (extracted_text, pdf_path) - Extracted text and path to the converted PDF
    """
    # Get filename from object or argument
    if hasattr(file_object, 'filename'):
        file_name = file_object.filename
    else:
        file_name = filename or os.path.basename(file_object)
    
    file_name = file_name.lower()
    temp_dir = None
    temp_input_path = None
    temp_output_path = None
    
    try:
        # For PDF files, extract text directly
        if file_name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(file_object)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text, file_object if isinstance(file_object, str) else None
        
        # For other files, convert to PDF first using CloudConvert
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save the file to a temporary location
        if hasattr(file_object, 'save'):
            # Handle Flask file objects
            temp_input_path = os.path.join(temp_dir, os.path.basename(file_name))
            file_object.save(temp_input_path)
        elif isinstance(file_object, str) and os.path.exists(file_object):
            # Handle file paths
            temp_input_path = file_object
        elif hasattr(file_object, 'read') and callable(file_object.read):
            # Handle standard file objects (like those returned by open())
            temp_input_path = os.path.join(temp_dir, os.path.basename(file_name))
            with open(temp_input_path, 'wb') as f:
                f.write(file_object.read())
                # Reset the file pointer to the beginning for potential further use
                file_object.seek(0)
        else:
            raise ValueError("Unsupported file object type")
        
        # Initialize CloudConvert
        api_key = os.getenv('CLOUDCONVERT_API_KEY')
        if not api_key:
            raise ValueError("CLOUDCONVERT_API_KEY environment variable not set")
        cloudconvert.configure(api_key=api_key, sandbox=False)
        
        # Create a job with upload task
        job = cloudconvert.Job.create(payload={
            'tasks': {
                'upload-file': {
                    'operation': 'import/upload'
                },
                'convert-file': {
                    'operation': 'convert',
                    'input': 'upload-file',
                    'output_format': 'pdf'
                },
                'export-file': {
                    'operation': 'export/url',
                    'input': 'convert-file'
                }
            }
        })
        
        # Find the upload task ID
        upload_task_id = None
        for task in job['tasks']:
            if task['operation'] == 'import/upload':
                upload_task_id = task['id']
                break
        
        # Get the upload task and upload the file
        upload_task = cloudconvert.Task.find(id=upload_task_id)
        cloudconvert.Task.upload(file_name=temp_input_path, task=upload_task)
        
        # Wait for the job to finish
        job_info = cloudconvert.Job.wait(id=job['id'])
        
        # Get the export task to find the download URL
        export_task = None
        for task in job_info['tasks']:
            if task['operation'] == 'export/url':
                export_task = task
                break
        
        # Download the converted PDF
        temp_output_path = os.path.join(temp_dir, "converted.pdf")
        cloudconvert.download(url=export_task['result']['files'][0]['url'], 
                              filename=temp_output_path)
        
        # Extract text from the converted PDF
        with open(temp_output_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        # Clean up only the input file, keep the PDF for displaying
        if temp_input_path != file_object and temp_input_path and os.path.exists(temp_input_path):
            try:
                os.remove(temp_input_path)
            except:
                pass
        
        # Return the text and the path to the PDF
        return text, temp_output_path
        
    except Exception as e:
        # Clean up temporary files in case of error
        if temp_dir and os.path.exists(temp_dir):
            if temp_input_path and os.path.exists(temp_input_path) and temp_input_path != file_object:
                try:
                    os.remove(temp_input_path)
                except:
                    pass
            if temp_output_path and os.path.exists(temp_output_path):
                try:
                    os.remove(temp_output_path)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass
        raise Exception(f"Failed to process file {file_name}: {str(e)}")

def process_file_to_text(file_object, filename=None):
    """
    Process any file to extract text, converting if necessary
    This function is maintained for backward compatibility
    
    Args:
        file_object: File object from request.files or a file path
        filename (str, optional): Name of the file if file_object doesn't have it
        
    Returns:
        str: Extracted text content
    """
    text, _ = convert_to_pdf_and_extract_text(file_object, filename)
    return text

def process_file_for_gpt(file_object, gpt_process_func, filename=None):
    """
    Process a file and send its text to GPT
    
    Args:
        file_object: File object from request.files or a file path
        gpt_process_func: Function to process text with GPT
        filename (str, optional): Name of the file if file_object doesn't have it
        
    Returns:
        dict: Result from GPT processing
    """
    # Convert to PDF and extract text
    text, pdf_path = convert_to_pdf_and_extract_text(file_object, filename)
    
    # Process text with GPT
    result = gpt_process_func([text])
    
    # Add additional information to result
    if result and len(result) > 0:
        # Add original filename
        if hasattr(file_object, 'filename'):
            result[0]["filename"] = file_object.filename
        elif filename:
            result[0]["filename"] = filename
            
        # Add PDF path if available
        if pdf_path:
            result[0]["pdf_path"] = pdf_path
    
    return result

def process_files_batch(files, gpt_process_func):
    """
    Process multiple files and send text from each to GPT
    
    Args:
        files: List of file objects from request.files
        gpt_process_func: Function to process text with GPT
        
    Returns:
        list: List of results from GPT processing
    """
    results = []
    
    for file in files:
        if not file.filename:
            continue
            
        try:
            file_results = process_file_for_gpt(file, gpt_process_func)
            if file_results and len(file_results) > 0:
                results.append(file_results[0])
        except Exception as e:
            print(f"Error processing {file.filename}: {str(e)}")
            # Continue with other files even if one fails
    
    return results 