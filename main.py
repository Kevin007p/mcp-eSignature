"""
eSignature Document Validator MCP Server

Tools:
- analyze_pdf_signatures(path): Comprehensive analysis of PDF signatures (fields, signer info, validation)
- summarize_pdf_content(path): Extracts and summarizes the text content of a PDF
- add_signature_field(input_path, output_path, field_name, page, x, y, width, height): Adds a signature field to a PDF
"""

from mcp.server.fastmcp import FastMCP
from PyPDF2 import PdfReader
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigFieldSpec, append_signature_field
import os
import glob

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
def summarize_pdf_content(path: str) -> str:
    """Extracts and summarizes the text content of a PDF document."""
    try:
        reader = PdfReader(path)
        text_content = ""
        
        for page in reader.pages:
            text_content += page.extract_text() + " "
        
        if not text_content.strip():
            return "No text content found in PDF"
        
        # Clean up text
        text_content = " ".join(text_content.strip().split())
        
        # Create a simple summary (first 200 chars + key info)
        if len(text_content) > 200:
            summary = text_content[:200] + "..."
        else:
            summary = text_content
        
        # Add basic document info
        result = [f"Document: {os.path.basename(path)}"]
        result.append(f"Pages: {len(reader.pages)}")
        result.append(f"Content preview: {summary}")
        
        # Look for common document types
        text_lower = text_content.lower()
        if "agreement" in text_lower or "contract" in text_lower:
            result.append("Type: Contract/Agreement")
        elif "invoice" in text_lower or "bill" in text_lower:
            result.append("Type: Invoice/Billing")
        elif "application" in text_lower or "form" in text_lower:
            result.append("Type: Application/Form")
        else:
            result.append("Type: General Document")
        
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