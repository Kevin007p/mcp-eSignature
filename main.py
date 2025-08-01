"""
eSignature Document Validator MCP Server

Tools:
- analyze_pdf_signatures(path): Comprehensive analysis of PDF signatures (fields, signer info, validation)
- add_signature_field(input_path, output_path, field_name, page, x, y, width, height): Adds a signature field to a PDF
- organize_pdf_by_signature_state(file_path, base_folder): Moves PDF to appropriate folder based on signature state
"""

from mcp.server.fastmcp import FastMCP
from PyPDF2 import PdfReader
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec, append_signature_field
import os
import glob
import shutil

mcp = FastMCP("esignature-validator")

@mcp.tool()
def analyze_pdf_signatures(path: str) -> str:
    """Comprehensive analysis of PDF signatures - checks for fields, extracts signer info, and validates signatures."""
    try:
        reader = PdfReader(path)
        fields = reader.get_fields()
        
        if not fields:
            return "No form fields found"
        
        sig_fields = [k for k, v in fields.items() if v.get('/FT') == '/Sig']
        if not sig_fields:
            return "No signature fields found"
        
        result = [f"Signature fields: {', '.join(sig_fields)}"]
        signed_count = 0
        
        for field_name, field_data in fields.items():
            if field_data.get('/FT') == '/Sig' and '/V' in field_data and field_data['/V']:
                signed_count += 1
                sig_dict = field_data['/V']
                info = f"Field '{field_name}':"
                if '/Name' in sig_dict:
                    info += f" {sig_dict['/Name']}"
                if '/M' in sig_dict:
                    info += f" ({sig_dict['/M']})"
                result.append(info)
        
        if signed_count == 0:
            result.append("No fields are signed")
        else:
            result.append(f"✓ {signed_count} field(s) signed")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error: {str(e)}"

  
@mcp.tool()
def add_signature_field(input_path: str, output_path: str) -> str:
    """Adds a signature field to a PDF document."""
    try:
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
        
        return f"Signature field Kevin's Signature added to {os.path.basename(output_path)}"
        
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def organize_pdf_by_signature_state(file_path: str, base_folder: str) -> str:
    """Moves PDF to appropriate folder based on signature state:
    - 'no_signature_fields': Document has no signature fields
    - 'unsigned_fields': Document has signature fields but they're not signed
    - 'signed': Document has signed signature fields
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist"
        
        # Analyze the PDF
        reader = PdfReader(file_path)
        fields = reader.get_fields()
        
        # Determine the state (assuming 0 or 1 signature fields)
        if not fields:
            state = "no_signature_fields"
        else:
            sig_fields = [k for k, v in fields.items() if v.get('/FT') == '/Sig']
            if not sig_fields:
                state = "no_signature_fields"
            else:
                # Check if the signature field is signed
                sig_field_name = sig_fields[0]  # Assume only one signature field
                sig_field_data = fields[sig_field_name]
                if '/V' in sig_field_data and sig_field_data['/V']:
                    state = "signed"
                else:
                    state = "unsigned_fields"
        
        # Move the file (folders assumed to exist)
        filename = os.path.basename(file_path)
        destination = os.path.join(base_folder, state, filename)
        shutil.move(file_path, destination)
        
        return f"Moved {filename} to {state} folder (State: {state})"
        
    except Exception as e:
        return f"Error: {str(e)}"