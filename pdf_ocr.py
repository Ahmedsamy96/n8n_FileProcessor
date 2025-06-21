import os
import tempfile
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Path to Poppler
POPPLER_PATH = r'C:\Program Files\poppler\bin'

@app.route('/process-pdfs', methods=['POST'])
def process_pdfs():
    try:
        # Debug: Print all files in request
        print("Files in request:", list(request.files.keys()))
        print("Form data:", list(request.form.keys()))
        print("Content type:", request.content_type)
        
        # Check if any file exists in the request
        if not request.files:
            return jsonify({'error': 'No files in the request'}), 400
        
        # Try to get file0 first, then try other common names
        file = None
        file_key = None
        
        # Try different possible file keys
        possible_keys = ['file0', 'file', 'upload', 'document', 'pdf']
        
        for key in possible_keys:
            if key in request.files:
                file = request.files[key]
                file_key = key
                break
        
        # If still no file found, get the first file available
        if not file and request.files:
            file_key = list(request.files.keys())[0]
            file = request.files[file_key]
        
        if not file:
            return jsonify({'error': 'No file found in request'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        print(f"Found file: {file.filename} with key: {file_key}")

        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)

            # Read PDF bytes
            pdf_bytes = file.read()
            
            print(f"PDF size: {len(pdf_bytes)} bytes")

            # Convert PDF to images
            pages = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)
            
            print(f"Converted to {len(pages)} pages")

            # Perform OCR on each page
            page_texts = []
            for i, page in enumerate(pages):
                print(f"Processing page {i+1}")
                text = pytesseract.image_to_string(page)
                page_texts.append(text.strip())

            result = {
                'info': f"Title: {filename}",
                'text': ' '.join(page_texts),
                'pages': len(pages),
                'file_key_used': file_key
            }

            return jsonify(result)

        return jsonify({
            'info': f"Title: {secure_filename(file.filename)}",
            'error': 'Uploaded file is not a PDF'
        }), 400

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'service': 'pdf-ocr-service'})

@app.route('/test-upload', methods=['POST'])
def test_upload():
    """Test endpoint to debug file uploads"""
    try:
        print("=== DEBUG INFO ===")
        print("Content-Type:", request.content_type)
        print("Files:", list(request.files.keys()))
        print("Form:", list(request.form.keys()))
        print("Args:", list(request.args.keys()))
        
        result = {
            'content_type': request.content_type,
            'files': list(request.files.keys()),
            'form': list(request.form.keys()),
            'args': list(request.args.keys())
        }
        
        if request.files:
            for key, file in request.files.items():
                result[f'file_{key}'] = {
                    'filename': file.filename,
                    'content_type': file.content_type,
                    'size': len(file.read()) if file else 0
                }
                file.seek(0)  # Reset file pointer
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))

    if not os.path.exists(POPPLER_PATH):
        print(f"Warning: Poppler path not found at {POPPLER_PATH}")
        print("Please update the POPPLER_PATH variable in the script")

    try:
        pytesseract.get_tesseract_version()
        print("Tesseract is properly configured.")
    except Exception as e:
        print(f"Error: Tesseract is not properly installed or configured: {e}")
        exit(1)

    app.run(host='0.0.0.0', port=port, debug=True)