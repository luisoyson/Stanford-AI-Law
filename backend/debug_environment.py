"""
Debug script to check environment variables and API keys
"""

import os
import sys
from dotenv import load_dotenv

# Get absolute path to the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

# Load environment variables from the root .env file
env_path = os.path.join(root_dir, ".env")
print(f"Loading .env file from: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

load_dotenv(env_path)

# Check OpenAI API key
openai_key = os.getenv("OPEN_AI_API_KEY")
if openai_key:
    print("OPEN_AI_API_KEY found in environment variables")
    # Print first few characters to verify
    print(f"Key starts with: {openai_key[:8]}...")
else:
    print("WARNING: OPEN_AI_API_KEY not found in environment variables")

# Check CloudConvert API key
cloudconvert_key = os.getenv("CLOUDCONVERT_API_KEY")
if cloudconvert_key:
    print("CLOUDCONVERT_API_KEY found in environment variables")
    # Print first few characters to verify
    print(f"Key starts with: {cloudconvert_key[:8]}...")
else:
    print("WARNING: CLOUDCONVERT_API_KEY not found in environment variables")

# List all API-related environment variables
print("\nAll API-related environment variables:")
for key in os.environ:
    if "API" in key:
        value = os.environ[key]
        print(f"{key}: {value[:8]}..." if value else f"{key}: None")

print("\nPython path:")
for path in sys.path:
    print(path)

# Try to import the required modules
print("\nChecking module imports:")
try:
    import openai
    print("✓ openai module imported successfully")
except ImportError as e:
    print(f"✗ Error importing openai: {e}")

try:
    import cloudconvert
    print("✓ cloudconvert module imported successfully")
except ImportError as e:
    print(f"✗ Error importing cloudconvert: {e}")

try:
    from API_services.gpt import GPT_Process_PDFs
    print("✓ GPT_Process_PDFs imported successfully")
except ImportError as e:
    print(f"✗ Error importing GPT_Process_PDFs: {e}")

try:
    from API_services.cloud_convert import convert_to_pdf_and_extract_text
    print("✓ convert_to_pdf_and_extract_text imported successfully")
except ImportError as e:
    print(f"✗ Error importing convert_to_pdf_and_extract_text: {e}")

print("\nDebug complete!") 