from flask import Flask, request, jsonify, render_template_string
import requests
import os
import json
import re
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

# n8n Webhook URL
WEBHOOK_URL = "http://localhost:5678/webhook/DOC-OCR"

# Configuration
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'txt "\[0:14\]": "txt",', 'pdf', 'doc', 'docx', 'csv', 'json', 'xml', 'html', 'md', 'py', 'js', 'css', 'xlsx', 'xls', 'png', 'jpg', 'jpeg'}

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def parse_resume_data(text_content):
    """Parse resume/CV text content and extract structured information"""
    if not text_content:
        return None
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text_content)
    
    phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
    phones = re.findall(phone_pattern, text_content)
    
    linkedin_pattern = r'linkedin\.com/in/[\w-]+'
    linkedin = re.findall(linkedin_pattern, text_content.lower())
    
    lines = text_content.split('\n')
    potential_name = None
    for line in lines[:5]:
        line = line.strip()
        if line and len(line.split()) <= 4 and any(word[0].isupper() for word in line.split() if word):
            potential_name = line
            break
    
    return {
        'name': potential_name,
        'emails': emails,
        'phones': phones,
        'linkedin': linkedin[0] if linkedin else None,
        'raw_text': text_content
    }

# Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Supported types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
            
        filename = secure_filename(file.filename)
        temp_path = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(temp_path)
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'file': (filename, f, file.content_type)}
                data = {
                    'filename': filename,
                    'content_type': file.content_type,
                    'file_size': os.path.getsize(temp_path)
                }
                response = requests.post(WEBHOOK_URL, files=files, data=data, timeout=30)
                
            os.remove(temp_path)
            
            if response.status_code != 200:
                return jsonify({'error': f'n8n webhook returned status {response.status_code}: {response.text}'}), 500
                
            # Get raw response
            try:
                response_data = response.json()
                # If JSON, convert to string for parsing
                raw_text = json.dumps(response_data, ensure_ascii=False)
            except:
                raw_text = response.text
                
            # Parse the raw response for resume data
            parsed_data = parse_resume_data(raw_text)
            
            return jsonify({
                'success': True,
                'message': 'File processed successfully',
                'filename': filename,
                'response': parsed_data or {'raw_text': raw_text},
                'raw_response': raw_text
            })
            
        except requests.RequestException as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': f'Failed to connect to n8n: {str(e)}'}), 500
            
    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'File upload API is running'})

# HTML template (same as provided, with updated JavaScript)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Processor - Professional OCR & Text Extraction</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        .main-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            backdrop-filter: blur(10px);
        }
        .upload-section {
            padding: 40px;
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
            border-bottom: 1px solid #e0e6ed;
        }
        .upload-area {
            border: 3px dashed #cbd5e0;
            border-radius: 15px;
            padding: 60px 40px;
            text-align: center;
            background: white;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .upload-area:hover {
            border-color: #4299e1;
            background: #f7fafc;
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        }
        .upload-area.dragover {
            border-color: #48bb78;
            background: #f0fff4;
            transform: scale(1.02);
        }
        .upload-icon {
            font-size: 4rem;
            color: #a0aec0;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        .upload-area:hover .upload-icon {
            color: #4299e1;
            transform: scale(1.1);
        }
        .upload-text {
            font-size: 1.2rem;
            color: #2d3748;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .upload-subtext {
            color: #718096;
            margin-bottom: 30px;
        }
        .file-input-wrapper {
            position: relative;
            display: inline-block;
            margin-bottom: 20px;
        }
        .file-input {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        .file-input-button {
            background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(66, 153, 225, 0.3);
        }
        .file-input-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(66, 153, 225, 0.4);
        }
        .selected-file {
            margin: 20px 0;
            padding: 15px;
            background: #edf2f7;
            border-radius: 10px;
            display: none;
        }
        .selected-file.show {
            display: block;
        }
        .file-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .file-icon {
            font-size: 2rem;
            color: #4299e1;
        }
        .file-details h4 {
            color: #2d3748;
            margin-bottom: 5px;
        }
        .file-details p {
            color: #718096;
            font-size: 0.9rem;
        }
        .upload-button {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
            display: none;
        }
        .upload-button.show {
            display: inline-block;
        }
        .upload-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(72, 187, 120, 0.4);
        }
        .upload-button:disabled {
            background: #a0aec0;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .loading {
            display: none;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        .loading.show {
            display: flex;
        }
        .spinner {
            width: 30px;
            height: 30px;
            border: 3px solid #e2e8f0;
            border-top: 3px solid #4299e1;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .results-section {
            padding: 40px;
            display: none;
        }
        .results-section.show {
            display: block;
        }
        .results-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }
        .results-header h2 {
            color: #2d3748;
            font-size: 1.8rem;
            font-weight: 700;
        }
        .success-badge {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        .results-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        @media (max-width: 768px) {
            .results-grid {
                grid-template-columns: 1fr;
            }
        }
        .info-card, .text-card {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            border-left: 5px solid #4299e1;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        .info-card h3, .text-card h3 {
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 1.3rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .info-item {
            margin-bottom: 15px;
            padding: 12px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }
        .info-label {
            font-weight: 600;
            color: #4a5568;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        .info-value {
            color: #2d3748;
            font-size: 1rem;
            word-break: break-all;
        }
        .info-value a {
            color: #4299e1;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        .info-value a:hover {
            color: #3182ce;
        }
        .text-content {
            background: white;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace;
            line-height: 1.8;
            color: #2d3748;
            max-height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.02);
        }
        .raw-response {
            background: #2d3748;
            color: #e2e8f0;
            padding: 25px;
            border-radius: 12px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.3);
        }
        .actions {
            display: flex;
            gap: 15px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
        }
        .action-button {
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .action-button.primary {
            background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(66, 153, 225, 0.3);
        }
        .action-button.secondary {
            background: #e2e8f0;
            color: #4a5568;
        }
        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(66, 153, 225, 0.4);
        }
        .error {
            background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
            color: #c53030;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            display: none;
            border-left: 5px solid #e53e3e;
        }
        .error.show {
            display: block;
        }
        .supported-formats {
            margin-top: 20px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 12px;
            text-align: left;
        }
        .supported-formats h4 {
            color: #2d3748;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .format-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .format-tag {
            background: #4299e1;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e2e8f0;
            border-radius: 2px;
            overflow: hidden;
            margin: 20px 0;
            display: none;
        }
        .progress-bar.show {
            display: block;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4299e1, #48bb78);
            border-radius: 2px;
            transition: width 0.3s ease;
            animation: progress-animation 2s ease-in-out infinite;
        }
        @keyframes progress-animation {
            0%, 100% { width: 30%; }
            50% { width: 80%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-file-alt"></i> Document Processor</h1>
            <p>Professional OCR & Text Extraction Service</p>
        </div>
        <div class="main-card">
            <div class="upload-section">
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="upload-area" id="uploadArea">
                        <i class="fas fa-cloud-upload-alt upload-icon"></i>
                        <div class="upload-text">Drop your file here or click to browse</div>
                        <div class="upload-subtext">Supports documents, images, and text files up to 16MB</div>
                        <div class="file-input-wrapper">
                            <input type="file" id="fileInput" name="file" class="file-input" required>
                            <button type="button" class="file-input-button">
                                <i class="fas fa-folder-open"></i> Choose File
                            </button>
                        </div>
                        <div class="selected-file" id="selectedFile">
                            <div class="file-info">
                                <i class="fas fa-file file-icon" id="fileIcon"></i>
                                <div class="file-details">
                                    <h4 id="fileName"></h4>
                                    <p id="fileSize"></p>
                                </div>
                            </div>
                        </div>
                        <button type="submit" class="upload-button" id="uploadButton">
                            <i class="fas fa-paper-plane"></i> Process Document
                        </button>
                        <div class="progress-bar" id="progressBar">
                            <div class="progress-fill"></div>
                        </div>
                        <div class="loading" id="loading">
                            <div class="spinner"></div>
                            <span>Processing your document...</span>
                        </div>
                        <div class="supported-formats">
                            <h4><i class="fas fa-info-circle"></i> Supported Formats</h4>
                            <div class="format-tags">
                                <span class="format-tag">PDF</span>
                                <span class="format-tag">DOC/DOCX</span>
                                <span class="format-tag">TXT</span>
                                <span class="format-tag">CSV</span>
                                <span class="format-tag">JSON</span>
                                <span class="format-tag">XML</span>
                                <span class="format-tag">HTML</span>
                                <span class="format-tag">MD</span>
                                <span class="format-tag">PNG/JPG</span>
                                <span class="format-tag">XLS/XLSX</span>
                            </div>
                        </div>
                    </div>
                </form>
                <div class="error" id="errorDiv"></div>
            </div>
            <div class="results-section" id="resultsSection">
                <div class="results-header">
                    <i class="fas fa-check-circle" style="color: #48bb78; font-size: 2rem;"></i>
                    <h2>Extraction Results</h2>
                    <div class="success-badge">
                        <i class="fas fa-magic"></i> Processed Successfully
                    </div>
                </div>
                <div class="results-grid">
                    <div class="info-card" id="infoCard">
                        <h3><i class="fas fa-info-circle"></i> Document Information</h3>
                        <div id="documentInfo"></div>
                    </div>
                    <div class="text-card">
                        <h3><i class="fas fa-file-text"></i> Extracted Content</h3>
                        <div class="text-content" id="extractedText"></div>
                    </div>
                </div>
                <div class="info-card">
                    <h3><i class="fas fa-code"></i> Raw Response</h3>
                    <div class="raw-response" id="rawResponse"></div>
                </div>
                <div class="actions">
                    <button class="action-button primary" onclick="copyToClipboard()">
                        <i class="fas fa-copy"></i> Copy Text
                    </button>
                    <button class="action-button secondary" onclick="downloadText()">
                        <i class="fas fa-download"></i> Download
                    </button>
                    <button class="action-button secondary" onclick="resetForm()">
                        <i class="fas fa-redo"></i> Process Another
                    </button>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        let extractedContent = '';
        let currentFileName = '';
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');
        const selectedFile = document.getElementById('selectedFile');
        const uploadButton = document.getElementById('uploadButton');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect();
            }
        });
        fileInput.addEventListener('change', handleFileSelect);
        function handleFileSelect() {
            const file = fileInput.files[0];
            if (file) {
                document.getElementById('fileName').textContent = file.name;
                document.getElementById('fileSize').textContent = formatFileSize(file.size);
                const extension = file.name.split('.').pop().toLowerCase();
                const iconMap = {
                    'pdf': 'fas fa-file-pdf',
                    'doc': 'fas fa-file-word',
                    'docx': 'fas fa-file-word',
                    'txt': 'fas fa-file-alt',
                    'csv': 'fas fa-file-csv',
                    'json': 'fas fa-file-code',
                    'xml': 'fas fa-file-code',
                    'html': 'fas fa-file-code',
                    'png': 'fas fa-file-image',
                    'jpg': 'fas fa-file-image',
                    'jpeg': 'fas fa-file-image',
                    'xls': 'fas fa-file-excel',
                    'xlsx': 'fas fa-file-excel'
                };
                document.getElementById('fileIcon').className = iconMap[extension] || 'fas fa-file';
                selectedFile.classList.add('show');
                uploadButton.classList.add('show');
                currentFileName = file.name;
            }
        }
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        function showError(message) {
            const errorDiv = document.getElementById('errorDiv');
            errorDiv.textContent = message;
            errorDiv.classList.add('show');
        }
        function displayResults(data) {
            const resultsSection = document.getElementById('resultsSection');
            const documentInfo = document.getElementById('documentInfo');
            const extractedText = document.getElementById('extractedText');
            const rawResponse = document.getElementById('rawResponse');
            extractedContent = data.raw_response || '';
            let infoHTML = `
                <div class="info-item">
                    <div class="info-label">File Name</div>
                    <div class="info-value">${data.filename}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">File Size</div>
                    <div class="info-value">${formatFileSize(data.response.file_size || 0)}</div>
                </div>
            `;
            if (data.response && typeof data.response === 'object') {
                if (data.response.name) {
                    infoHTML += `
                        <div class="info-item">
                            <div class="info-label">Candidate Name</div>
                            <div class="info-value">${data.response.name}</div>
                        </div>
                    `;
                }
                if (data.response.emails && data.response.emails.length > 0) {
                    infoHTML += `
                        <div class="info-item">
                            <div class="info-label">Email</div>
                            <div class="info-value">
                                ${data.response.emails.map(email => `<a href="mailto:${email}">${email}</a>`).join(', ')}
                            </div>
                        </div>
                    `;
                }
                if (data.response.phones && data.response.phones.length > 0) {
                    infoHTML += `
                        <div class="info-item">
                            <div class="info-label">Phone</div>
                            <div class="info-value">${data.response.phones.join(', ')}</div>
                        </div>
                    `;
                }
                if (data.response.linkedin) {
                    infoHTML += `
                        <div class="info-item">
                            <div class="info-label">LinkedIn</div>
                            <div class="info-value">
                                <a href="https://${data.response.linkedin}" target="_blank">${data.response.linkedin}</a>
                            </div>
                        </div>
                    `;
                }
            }
            documentInfo.innerHTML = infoHTML;
            extractedText.textContent = extractedContent || 'No text content extracted';
            extractedText.innerHTML = marked.parse(extractedContent || 'No text content extracted');
            rawResponse.textContent = extractedContent || 'No response received';
            resultsSection.classList.add('show');
            window.scrollTo({
                top: resultsSection.offsetTop,
                behavior: 'smooth'
            });
        }
        function copyToClipboard() {
            if (!extractedContent) {
                showError('No text to copy');
                return;
            }
            const textarea = document.createElement('textarea');
            textarea.value = extractedContent;
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                alert('Text copied to clipboard!');
            } catch (err) {
                showError('Failed to copy text to clipboard');
            }
            document.body.removeChild(textarea);
        }
        function downloadText() {
            if (!extractedContent) {
                showError('No text to download');
                return;
            }
            const blob = new Blob([extractedContent], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentFileName ? currentFileName.replace(/\.[^/.]+$/, '') + '_extracted.txt' : 'extracted_text.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
        function resetForm() {
            document.getElementById('uploadForm').reset();
            selectedFile.classList.remove('show');
            uploadButton.classList.remove('show');
            document.getElementById('resultsSection').classList.remove('show');
            document.getElementById('errorDiv').classList.remove('show');
            extractedContent = '';
            currentFileName = '';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        document.querySelector('.file-input-button').addEventListener('click', () => {
            fileInput.click();
        });
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('fileInput');
            const uploadBtn = document.getElementById('uploadButton');
            const loading = document.getElementById('loading');
            const progressBar = document.getElementById('progressBar');
            const errorDiv = document.getElementById('errorDiv');
            const resultsSection = document.getElementById('resultsSection');
            if (!fileInput.files[0]) {
                showError('Please select a file');
                return;
            }
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            loading.classList.add('show');
            progressBar.classList.add('show');
            errorDiv.classList.remove('show');
            resultsSection.classList.remove('show');
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (response.ok) {
                    displayResults(data);
                } else {
                    showError(data.error);
                }
            } catch (error) {
                showError(`Network error: ${error.message}`);
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Process Document';
                loading.classList.remove('show');
                progressBar.classList.remove('show');
            }
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)