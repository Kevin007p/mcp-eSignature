# eSignature Document Validator MCP Server

Tools:
- analyze_pdf_signatures(path): Comprehensive analysis of PDF signatures (fields, signer info, validation)
- add_signature_field(input_path, output_path=None): Adds a signature field to a PDF and moves it to unsigned_fields folder
- organize_pdf_by_signature_state(file_path, base_folder=None): Moves PDF to appropriate folder based on signature state
- check_unsigned_folder_for_updates(): Automatically checks unsigned_fields folder for newly signed documents

Resources:
- pdf://documents: Access to PDF documents directory
- pdf://organized: Access to organized PDF folders (no_signature_fields, unsigned_fields, signed)
