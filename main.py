from mcp.server.fastmcp import FastMCP
from PyPDF2 import PdfReader
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec, append_signature_field
import os
import glob
import shutil

mcp = FastMCP("esignature-validator")

PDF_DOCUMENTS_DIR = "pdf_documents"
ORGANIZED_FOLDERS_DIR = "organized_pdfs"

### HELP FUNCTIONS ###

def find_file_in_organized_folders(filename):
    """Helper function to find a file in any organized folder or pdf_documents"""
    possible_paths = [
        os.path.join(ORGANIZED_FOLDERS_DIR, "no_signature_fields", filename),
        os.path.join(ORGANIZED_FOLDERS_DIR, "unsigned_fields", filename),
        os.path.join(ORGANIZED_FOLDERS_DIR, "signed", filename),
        os.path.join(PDF_DOCUMENTS_DIR, filename)
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def analyze_signature_state(pdf_path):
    """Helper function to analyze PDF signature state and return the appropriate folder name"""
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()
    
    if not fields:
        return "no_signature_fields"
    
    sig_fields = [k for k, v in fields.items() if v.get('/FT') == '/Sig']
    if not sig_fields:
        return "no_signature_fields"
    
    # Check if the signature field is signed
    sig_field_name = sig_fields[0]  # Assume only one signature field
    sig_field_data = fields[sig_field_name]
    if '/V' in sig_field_data and sig_field_data['/V']:
        return "signed"
    else:
        return "unsigned_fields"


### RESOURCES ###

@mcp.resource("pdf://documents")
def get_pdf_documents():
    """Expose PDF documents directory as a resource"""
    pdf_files = glob.glob(os.path.join(PDF_DOCUMENTS_DIR, "*.pdf"))
    return {
        "name": "PDF Documents",
        "description": f"PDF files in {PDF_DOCUMENTS_DIR} directory",
        "files": [os.path.basename(f) for f in pdf_files],
        "directory": PDF_DOCUMENTS_DIR
    }

@mcp.resource("pdf://organized")
def get_organized_pdfs():
    """Expose organized PDF folders as resources"""
    
    folders = ["no_signature_fields", "unsigned_fields", "signed"]
    folder_contents = {}
    
    for folder in folders:
        folder_path = os.path.join(ORGANIZED_FOLDERS_DIR, folder)
        pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
        folder_contents[folder] = [os.path.basename(f) for f in pdf_files]
    
    return {
        "name": "Organized PDFs",
        "description": "PDFs organized by signature state",
        "folders": folder_contents,
        "base_directory": ORGANIZED_FOLDERS_DIR
    }


### TOOLS ###

@mcp.tool()
def analyze_pdf_signatures(path: str) -> str:
    """Comprehensive analysis of PDF signatures - checks for fields, extracts signer info, and validates signatures."""
    reader = PdfReader(path)
    fields = reader.get_fields()
    
    if not fields:
        return "No form fields found"
    
    sig_fields = [k for k, v in fields.items() if v.get('/FT') == '/Sig']
    if not sig_fields:
        return "No signature fields found"
    
    result = [f"Signature fields: {', '.join(sig_fields)}"]
    
    # Since we assume only 1 signature field
    field_name = sig_fields[0]
    field_data = fields[field_name]
    
    if '/V' in field_data and field_data['/V']:
        # It's signed
        sig_dict = field_data['/V']
        info = f"Field '{field_name}':"
        if '/Name' in sig_dict:
            info += f" {sig_dict['/Name']}"
        if '/M' in sig_dict:
            info += f" ({sig_dict['/M']})"
        result.append(info)
        result.append("✓ 1 field(s) signed")
    else:
        result.append("No fields are signed")
    
    return "\n".join(result)

@mcp.tool()
def organize_pdf_by_signature_state(file_path: str, base_folder: str = None) -> str:
    """Moves PDF to appropriate folder based on signature state:
    - 'no_signature_fields': Document has no signature fields
    - 'unsigned_fields': Document has signature fields but they're not signed
    - 'signed': Document has signed signature fields
    """
    # Use default organized folders directory if not specified
    if base_folder is None:
        base_folder = ORGANIZED_FOLDERS_DIR
        
    # Find the file if it doesn't exist at the exact path
    if not os.path.exists(file_path):
        filename = os.path.basename(file_path)
        found_path = find_file_in_organized_folders(filename)
        if found_path:
            file_path = found_path
        else:
            return f"Error: Could not find file '{filename}' in any expected location"
    
    # Analyze the PDF to determine state
    state = analyze_signature_state(file_path)
    
    # Move the file
    filename = os.path.basename(file_path)
    destination = os.path.join(base_folder, state, filename)
    
    shutil.move(file_path, destination)
    
    return f"Moved {filename} to {state} folder (State: {state})"

@mcp.tool()
def add_signature_field(input_path: str, output_path: str = None) -> str:
    """Adds a signature field to a PDF document and moves it to the unsigned_fields folder."""
    # Find the file if it doesn't exist at the exact path
    if not os.path.exists(input_path):
        filename = os.path.basename(input_path)
        found_path = find_file_in_organized_folders(filename)
        if found_path:
            input_path = found_path
        else:
            return f"Error: Could not find file '{filename}' in any expected location"
    
    # Set output path to unsigned_fields folder
    if output_path is None:
        filename = os.path.basename(input_path)
        output_path = os.path.join(ORGANIZED_FOLDERS_DIR, "unsigned_fields", filename)
    
    # Add signature field
    with open(input_path, 'rb') as inf:
        writer = IncrementalPdfFileWriter(inf)
        sig_field_spec = SigFieldSpec(
            sig_field_name="Kevin's Signature",
            box=(400, 50, 600, 100),
            on_page=0
        )
        append_signature_field(writer, sig_field_spec)
        with open(output_path, 'wb') as outf:
            writer.write(outf)
    
    # Remove original file if it was in an organized folder
    if input_path != output_path and os.path.exists(input_path):
        os.remove(input_path)
    
    return f"Signature field Kevin's Signature added to {os.path.basename(output_path)} and moved to unsigned_fields folder"


@mcp.tool()
def check_unsigned_folder_for_updates() -> str:
    """Checks the unsigned_fields folder for documents that have been signed and moves them to the signed folder.
    This is useful after manually signing documents in Adobe Acrobat."""
    unsigned_folder = os.path.join(ORGANIZED_FOLDERS_DIR, "unsigned_fields")
    
    # Get all PDF files in the unsigned_fields folder
    pdf_files = glob.glob(os.path.join(unsigned_folder, "*.pdf"))
    
    if not pdf_files:
        return "No PDF files found in unsigned_fields folder"
    
    moved_files = []
    remaining_files = []
    
    for pdf_file in pdf_files:
        # Analyze the PDF to check if it's now signed
        state = analyze_signature_state(pdf_file)
        
        if state == "signed":
            # Document is signed! Move it to signed folder
            filename = os.path.basename(pdf_file)
            destination = os.path.join(ORGANIZED_FOLDERS_DIR, "signed", filename)
            
            shutil.move(pdf_file, destination)
            moved_files.append(filename)
        else:
            # Document is not signed
            remaining_files.append(os.path.basename(pdf_file))
    
    # Build the result message
    result = []
    
    if moved_files:
        result.append(f"Moved {len(moved_files)} signed document(s) to signed folder:")
        for filename in moved_files:
            result.append(f"  - {filename}")
    
    if remaining_files:
        result.append(f"{len(remaining_files)} document(s) still awaiting signature:")
        for filename in remaining_files:
            result.append(f"  - {filename}")
    
    if not moved_files and not remaining_files:
        result.append("No documents found in unsigned_fields folder")
    
    return "\n".join(result)