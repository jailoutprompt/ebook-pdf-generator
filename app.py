"""
eBook PDF Generator - 텍스트를 30페이지 전자책 PDF로 변환
"""

import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename

from generator.pdf_maker import generate_ebook

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB
app.config["UPLOAD_FOLDER"] = Path(__file__).parent / "uploads"
app.config["OUTPUT_FOLDER"] = Path(__file__).parent / "output"

ALLOWED_EXTENSIONS = {"txt", "docx"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _extract_text_from_file(filepath: str) -> str:
    """업로드된 파일에서 텍스트를 추출한다."""
    ext = filepath.rsplit(".", 1)[1].lower()
    if ext == "txt":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    elif ext == "docx":
        from docx import Document
        doc = Document(filepath)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return ""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    title = request.form.get("title", "").strip() or "나의 전자책"
    author = request.form.get("author", "").strip() or "저자 미상"
    text = request.form.get("text", "").strip()

    # 파일 업로드 처리
    file = request.files.get("file")
    if file and file.filename and _allowed_file(file.filename):
        app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
        filename = secure_filename(file.filename)
        filepath = str(app.config["UPLOAD_FOLDER"] / filename)
        file.save(filepath)
        file_text = _extract_text_from_file(filepath)
        os.remove(filepath)
        if file_text:
            text = file_text if not text else text + "\n\n" + file_text

    if not text:
        return jsonify({"error": "텍스트를 입력하거나 파일을 업로드해주세요."}), 400

    # PDF 생성
    app.config["OUTPUT_FOLDER"].mkdir(parents=True, exist_ok=True)
    output_name = f"ebook_{uuid.uuid4().hex[:8]}.pdf"
    output_path = str(app.config["OUTPUT_FOLDER"] / output_name)

    try:
        generate_ebook(title, author, text, output_path)
    except Exception as e:
        return jsonify({"error": f"PDF 생성 중 오류가 발생했습니다: {str(e)}"}), 500

    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"{title}.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
