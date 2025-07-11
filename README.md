# n8n_FileProcessor
# 🧠 Workflow Breakdown

A detailed explanation of the n8n OCR web app that extracts text from uploaded files, either using native PDF text extraction or OCR via Tesseract.

---

![n8n OCR Workflow](https://github.com/Ahmedsamy96/n8n_FileProcessor/blob/main/img/n8n_workflow.png)

---

## 🔄 Step-by-Step Explanation

### 1. **Webhook (Trigger)**
- **Purpose**: Accepts incoming HTTP POST requests from the front-end web UI.
- **Input**: PDF or image file uploaded by the user.
- **Output**: File metadata and content passed to the next node.

---

### 2. **Edit Fields**
- **Purpose**: Used to rename or prepare incoming data (e.g., extract file content or metadata).
- **Note**: Often used to isolate the binary file input or normalize MIME types.

---

### 3. **Extract from File1 (Extract from PDF)**
- **Purpose**: Attempts direct text extraction from the uploaded PDF.
- **Used for**: Text-based PDFs (searchable).

---

### 4. **If Node**
- **Purpose**: Checks if the `Extract from PDF` step successfully returned any text.
- **Condition**:
  - ✅ **True**: Text exists → continue without OCR.
  - ❌ **False**: Text not found → switch to OCR using external API.

---

### 5. **HTTP Request (OCR API via Tesseract)**
- **Purpose**: Sends image/PDF to an OCR API (e.g., Tesseract server) to extract text.
- **Input**: Raw binary or base64 content of the uploaded file.
- **Output**: Text extracted from scanned images or non-searchable PDFs.

---

### 6. **Merge Node**
- **Purpose**: Merges the output of either the Extract from PDF or the OCR API.
- **Mode**: `append` mode, ensuring one output path for all files regardless of the method used.

---

### 7. **Edit Fields2**
- **Purpose**: Formats or renames the merged result fields (e.g., unify output field name like `extracted_text`).

---

### 8. **Respond to Webhook**
- **Purpose**: Sends the extracted text back to the front-end web application.
- **Behavior**: Closes the request-response loop, allowing the UI to display results to the user.

---
### **Final View:**
#### input
![n8n OCR Workflow](https://github.com/Ahmedsamy96/n8n_FileProcessor/blob/main/img/Web_UI_1.png)

#### output
![n8n OCR Workflow](https://github.com/Ahmedsamy96/n8n_FileProcessor/blob/main/img/Web_UI_2.png)


## ✅ Summary

- Supports both text-based and image-based files.
- Intelligent switching based on content type.
- Flexible integration with any front-end via webhook.

