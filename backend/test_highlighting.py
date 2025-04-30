import os
import sys
from API_services.gpt import GPT_Process_PDFs

def test_highlighting():
    """Test the sentence-by-sentence highlighting functionality"""
    
    # Sample text with multiple sentences of varying sensitivity
    sample_text = """CONFIDENTIAL MEMO
From: Legal Department
To: Executive Team
Subject: Acquisition of XYZ Corp

This memo outlines our strategy for the upcoming acquisition. The target company, XYZ Corp, is valued at approximately $50M. 
Our legal team has identified several potential risks in the transaction.

Attorney Jane Smith has advised that we proceed with caution due to potential antitrust concerns. The regulatory environment 
remains challenging but navigable. We should submit our proposal by June 15 to avoid complications.

Financial projections show Q3 revenue of $10.2M with an EBITDA of $3.4M. The CEO's SSN is 123-45-6789 for the background check.

Please direct any questions to john.doe@example.com.
"""
    
    # Process the text
    results = GPT_Process_PDFs([sample_text], ["test_document.txt"])
    
    # Check if we got results
    if results and len(results) > 0:
        html_output = results[0]["marked_content"]
        
        # Save the HTML result to a file
        with open("test_highlighting_result.html", "w") as f:
            f.write(html_output)
        
        print(f"Generated HTML file: test_highlighting_result.html")
        
        # Count the number of highlighted sections
        low_count = html_output.count('<mark class="low">')
        medium_count = html_output.count('<mark class="medium">')
        high_count = html_output.count('<mark class="high">')
        
        print(f"Highlighting statistics:")
        print(f"  - Low sensitivity: {low_count} marks")
        print(f"  - Medium sensitivity: {medium_count} marks")
        print(f"  - High sensitivity: {high_count} marks")
        print(f"  - Total highlights: {low_count + medium_count + high_count}")
        
        # Print a snippet of the marked content (first 500 chars)
        content_preview = html_output.replace("\n", " ").replace("  ", " ")
        print("\nPreview of the first part of marked content:")
        print(content_preview[:500] + "...")
    else:
        print("No results returned from GPT processing")

if __name__ == "__main__":
    # Add the parent directory to the path so we can import the API_services module
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    test_highlighting() 