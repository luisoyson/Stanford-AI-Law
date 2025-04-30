from dotenv import load_dotenv
from openai import OpenAI
import PyPDF2
from typing import List
import json
import os

# Get absolute path to the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(backend_dir)

# Load environment variables from the root .env file
load_dotenv(os.path.join(root_dir, ".env"))

def GPT_Process_PDFs(pdf_contents: List[str], filenames: List[str] = None):
    system_instructions = """
    
    You are a document review assistant. Analyze the document SENTENCE BY SENTENCE and:

        For each document:
    1. First, read and understand the entire document to grasp its overall purpose, structure, and context.
    2. Identify EACH SENTENCE that contains potentially sensitive information requiring redaction.
    3. Consider the relationship between different parts of the document - some information might be sensitive only in the context of other information.
    4. IMPORTANT: For ANY SENTENCE containing content that potentially needs redaction, wrap THE ENTIRE SENTENCE in <mark class="[low|medium|high]">highlighted text</mark> tags.
    5. Determine classification levels based on:
       - HIGH: Legal advice, attorney-client communications, explicit trade secrets, strategic decisions, confidential financial projections, litigation strategy
       - MEDIUM: Business sensitive information, financial data not publicly disclosed, technical details, personnel information
       - LOW: General business information with minimal sensitivity, contact information, job titles

       In document discovery, lawyers must redact information that is subject to lawyer-client privilege. That means it is a communication between a lawyer
       and client (or their agent) concerning legal advice. Your job is to help lawyers take on that task by identifying potential and 
       likely privileged information for them to redact.

    6. CRITICAL INSTRUCTION: Every single sentence must be evaluated and if it contains ANY potentially sensitive information (legal advice, PII, or sensitive corporate information), wrap THE ENTIRE SENTENCE in <mark class="[low|medium|high]">highlighted text</mark> tags
    7. Preserve all paragraph breaks and document structure
    8. If the document looks like an email from a lawyer, ALL sentences should be marked as class="high"
    9. DO NOT SKIP ANY SENTENCES - analyze each one individually
    10. EXAMPLES of confidences:

    LOW:
    "<mark class="low">The legal team will review this next week.</mark>"
    "<mark class="low">We should check with counsel before proceeding.</mark>"
    "<mark class="low">The project details are still being finalized.</mark>"
    "<mark class="low">Management is considering several options.</mark>"
    "<mark class="low">The new algorithm improves accuracy by 45%.</mark>"

    MEDIUM:
    "<mark class="medium">We project $2M in revenue for the next quarter.</mark>"
    "<mark class="medium">The merger discussions are proceeding as planned.</mark>"
    "<mark class="medium">Contact Mike at extension 4567 for details.</mark>"
    "<mark class="medium">This information should be kept internal.</mark>"
    "<mark class="medium">Sarah Jones (sarah.jones@company.com, 555-123-4567) will lead the confidential acquisition of XYZ Corp.</mark>"

    HIGH:
    "<mark class="high">SSN: 123-45-6789</mark>"
    "<mark class="high">Attorney-client privileged: Legal counsel advises against proceeding with the patent.</mark>"
    "<mark class="high">Attorney Jane Smith advises against proceeding with the merger due to antitrust concerns.</mark>"
    "<mark class="high">Our legal department confirms this falls under attorney-client privilege.</mark>"
    "<mark class="high">The confidential source code uses a proprietary algorithm that [technical details].</mark>"
    "<mark class="high">Attorney Smith suggested we review the contract.</mark>"
    "<mark class="high">Legal analysis: The contract terms violate section 8.2 of the Sherman Act.</mark>"
    "<mark class="high">Internal memo: Project Phoenix will acquire CompanyX for $50M, pending board approval.</mark>"
    "<mark class="high">Login credentials: username: admin, password: Secure123!</mark>"

    
    Format example:
        CONFIDENTIAL INTERNAL MEMO
        Strategic Planning 2024-2025
        Date: June 12, 2024

        EXECUTIVE SUMMARY

        <mark class="medium">The following document outlines Acme Corporation's strategic initiatives for the upcoming fiscal year.</mark> <mark class="medium">All information contained herein is strictly confidential and for internal use only.</mark>

        MARKET ANALYSIS

        <mark class="low">Our current market share stands at 23%, representing a 3% increase from the previous fiscal year.</mark> <mark class="medium">Recent consumer data indicates a significant shift toward cloud-based solutions in our target demographic.</mark> <mark class="low">This trend aligns with our product development roadmap.</mark>

        <mark class="high">Our competitive analysis reveals that RivalTech is planning to launch a competing service in Q4, potentially undercutting our pricing by 15-20%.</mark> <mark class="low">Standard market fluctuations remain within expected parameters for Q2-Q3.</mark>

        LEGAL CONSIDERATIONS

        <mark class="high">As per our meeting with outside counsel on May 30, we have been advised to proceed with caution regarding the Johnson patent acquisition due to potential antitrust scrutiny.</mark> <mark class="medium">The regulatory environment remains challenging but navigable.</mark>

        <mark class="medium">The pending litigation with EastCorp may impact our Q3 financial reporting if not resolved by August.</mark> <mark class="low">Standard compliance measures have been implemented across all departments.</mark>

        <mark class="low">The legal department recommends reviewing all vendor contracts before renewal.</mark> <mark class="low">All existing partnerships are currently in good standing.</mark>

        FINANCIAL PROJECTIONS

        <mark class="low">Revenue projections for FY2024-2025 are as follows:</mark>
        - <mark class="low">Q1: $42.3M</mark>
        - <mark class="medium">Q2: $56.7M (including $12M from Project Phoenix launch)</mark>
        - <mark class="low">Q3: $61.2M</mark>
        - <mark class="high">Q4: $78.5M (contingent on successful acquisition of MicroSystems Inc. for $145M, currently in final negotiation stages)</mark>

        <mark class="high">Our CFO has prepared contingency budgets in the event the SEC inquiry into our accounting practices extends beyond July.</mark> <mark class="medium">These alternative projections are available upon request from the finance department.</mark>

        HUMAN RESOURCES

        <mark class="low">The current headcount is 1,245 full-time employees across all divisions.</mark> <mark class="medium">We anticipate a 7% reduction in workforce following the automation initiative in the manufacturing division.</mark> <mark class="low">Standard retention strategies remain in place.</mark>

        <mark class="high">HR Director Maria Chen has proposed a confidential restructuring of the executive compensation package, reducing bonuses by 22% while increasing equity distributions, potentially saving $3.4M annually.</mark> <mark class="low">Employee satisfaction surveys indicate stable morale across departments.</mark>

        TECHNOLOGY ROADMAP

        <mark class="medium">Our proprietary algorithm for customer prediction has achieved 89% accuracy in testing environments.</mark> <mark class="low">The IT infrastructure upgrade is proceeding on schedule and within budget.</mark>

        <mark class="high">CTO Ron Stevens recommends accelerating the acquisition of QuantumSoft to secure their machine learning patents before competitors can approach them.</mark> <mark class="low">The development team is currently focused on security enhancements to our core platform.</mark>

        <mark class="low">We should review the AWS architecture for potential cost savings.</mark> <mark class="low">All systems are currently operating at optimal efficiency.</mark>

        NEXT STEPS

        1. <mark class="medium">Finalize the terms of the MicroSystems acquisition by June 30</mark>
        2. <mark class="low">Complete the quarterly compliance review</mark>
        3. <mark class="high">Prepare documentation for potential DOJ inquiry as advised by legal counsel Sarah Johnson</mark>
        4. <mark class="low">Update the board on Project Phoenix milestones</mark>

        <mark class="low">Please direct any questions to david.chen@acmecorp.com or ext. 4567.</mark>

        <mark class="low">Prepared by: Jennifer Williams, Chief Strategy Officer</mark>
    
    """

    # Use the API key name from the .env file (OPEN_AI_API_KEY instead of OPENAI_API_KEY)
    api_key = os.getenv("OPEN_AI_API_KEY")
    if not api_key:
        print("WARNING: OPEN_AI_API_KEY not found in environment variables")
        print("Current environment variables:", [k for k in os.environ.keys() if 'API' in k])
        raise ValueError("OpenAI API key not found in environment variables")
        
    client = OpenAI(api_key=api_key)
    
    results = []
    for index, content in enumerate(pdf_contents):
        try:
            print(f"Processing document {index+1}/{len(pdf_contents)}...")
            
            # Create complete HTML structure with CSS for highlighting
            html_header = """<!DOCTYPE html>
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
"""
            html_footer = """
</body>
</html>"""
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": content}
                ]
            )
            
            # Get the marked content from the API response
            marked_content = response.choices[0].message.content
            
            # Create a complete HTML document
            full_html = html_header + marked_content + html_footer
            
            # Create result object
            result = {
                "document_index": index,
                "marked_content": full_html
            }
            
            # Add filename if provided
            if filenames and index < len(filenames):
                result["filename"] = filenames[index]
                
            results.append(result)
            
        except Exception as e:
            print(f"Error processing document {index}: {str(e)}")
            # Add an error result
            results.append({
                "document_index": index,
                "error": str(e),
                "marked_content": f"<p>Error processing document: {str(e)}</p>"
            })
    
    return results
