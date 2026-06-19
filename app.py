from flask import Flask, request, send_file, jsonify, Response
from flask_cors import CORS
from tools.detector import detect_language
from tools.splitter import split_sentences
from tools.aligner import align_sentences
from tools.csv_generator import generate_csv
from tools.tmx_generator import generate_tmx
from tools.bilingual_to_aligned import process_bilingual_file
import io
import tempfile
import subprocess
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


LIBREOFFICE_PATH = "/usr/bin/libreoffice"   # adjust for your server
PDFTOTEXT_PATH = "/usr/bin/pdftotext"       # adjust for your server

app = Flask(__name__)
CORS(app)


def extract_text_from_uploaded_file(file_storage):
    ext = file_storage.filename.lower().split(".")[-1]
    logger.info(f"[EXTRACTOR] Uploaded file: {file_storage.filename}, ext={ext}")

    # Read raw bytes BEFORE save()
    file_storage.stream.seek(0)
    raw_bytes = file_storage.stream.read()
    logger.info(f"[EXTRACTOR] Raw bytes length BEFORE save: {len(raw_bytes)}")

    # If plain text, return immediately
    if ext not in ["doc", "docx", "pdf"]:
        try:
            text = raw_bytes.decode("utf-8")
            logger.info(f"[EXTRACTOR] Plain text length: {len(text)}")
            return text
        except Exception as e:
            logger.error(f"[EXTRACTOR] UTF-8 decode failed: {e}")
            return ""

    # Save to temp for external extractor
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_in:
        tmp_in.write(raw_bytes)
        input_path = tmp_in.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_out:
        output_path = tmp_out.name

    logger.info(f"[EXTRACTOR] Saved temp input: {input_path}")
    logger.info(f"[EXTRACTOR] Output path: {output_path}")

    try:
        if ext in ["doc", "docx"]:
            logger.info("[EXTRACTOR] Running DOC/DOCX extractor")
            subprocess.run(
                ["python", "tools/extractors/editable_text_extractor.py",
                 LIBREOFFICE_PATH, input_path, output_path],
                check=True
            )
        elif ext == "pdf":
            logger.info("[EXTRACTOR] Running PDF extractor")
            subprocess.run(
                ["python", "tools/extractors/pdf_text_extractor.py",
                 PDFTOTEXT_PATH, input_path, output_path],
                check=True
            )
    except Exception as e:
        logger.error(f"[EXTRACTOR] Extractor failed: {e}")
        return ""

    # Read extracted text
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            text = f.read()
        logger.info(f"[EXTRACTOR] Extracted text length: {len(text)}")
    except Exception as e:
        logger.error(f"[EXTRACTOR] Failed to read extracted text: {e}")
        text = ""

    # Cleanup
    os.remove(input_path)
    os.remove(output_path)

    return text


# -----------------------------
# NEW: Quick test endpoints
# -----------------------------

@app.route("/langdetect", methods=["GET"])
def langdetect_route():
    text = request.args.get("text", "")
    if not text:
        return jsonify({"error": "Missing ?text="}), 400
    lang = detect_language(text)
    return jsonify({"language": lang})


@app.route("/split", methods=["GET"])
def split_route():
    text = request.args.get("text", "")
    if not text:
        return jsonify({"error": "Missing ?text="}), 400
    sentences = split_sentences(text)
    return jsonify({"sentences": sentences})


@app.route("/align", methods=["GET"])
def align_route():
    src = request.args.get("src", "")
    tgt = request.args.get("tgt", "")
    if not src or not tgt:
        return jsonify({"error": "Missing ?src= and/or ?tgt="}), 400
    alignment = align_sentences(src, tgt)
    return jsonify({"alignment": alignment})

@app.route("/bilingualalign", methods=["GET"])
def bilingual_align_route():
    text = request.args.get("text", "")
    format = request.args.get("format", "csv")
    output = request.args.get("output", "alignment")  # alignment | failed

    if not text.strip():
        return "Error: Provide ?text=Your+text+here", 400

    result = process_bilingual_file(text)

    alignment = result["alignment"]
    failed_lines = result["failed_lines"]

    if output == "failed":
        failed_text = "\n".join(failed_lines)
        return Response(
            failed_text,
            mimetype="text/plain",
            headers={"Content-Disposition": "attachment; filename=failed_lines.txt"}
        )

    # Otherwise return alignment
    if format == "tmx":
        output_text = generate_tmx(alignment)
        mimetype = "application/xml"
        filename = "bilingual_alignment.tmx"
    else:
        output_text = generate_csv(alignment)
        mimetype = "text/csv"
        filename = "bilingual_alignment.csv"

    return Response(
        output_text,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# -----------------------------
# Your existing /process endpoint
# -----------------------------

@app.route("/process", methods=["POST"])
def process():
    mode = request.form.get("mode")
    format = request.form.get("format", "csv")
    file1 = request.files["file1"]
    text1 = extract_text_from_uploaded_file(file1)
    logger.info(f"[PROCESS] Mode={mode}, text1 length={len(text1)}")
    logger.info(f"[PROCESS] First 200 chars: {text1[:200]!r}")

    if mode == "langdetect":
        lang = detect_language(text1)
        output = f"Detected language: {lang}\n"
        return send_file(
            io.BytesIO(output.encode("utf-8")),
            as_attachment=True,
            download_name="langdetect.txt",
            mimetype="text/plain"
        )

    elif mode == "split":
        sentences = split_sentences(text1)
        output = "\n".join(sentences)
        return send_file(
            io.BytesIO(output.encode("utf-8")),
            as_attachment=True,
            download_name="sentences.txt",
            mimetype="text/plain"
        )

    elif mode == "align":
        file2 = request.files["file2"]
        text2 = extract_text_from_uploaded_file(file2)

        alignment = align_sentences(text1, text2)

        if format == "tmx":
            output_text = generate_tmx(alignment)
            mimetype = "application/xml"
            filename = "alignment.tmx"
        else:
            output_text = generate_csv(alignment)
            mimetype = "text/csv"
            filename = "alignment.csv"

        return Response(
            output_text,
            mimetype=mimetype,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    elif mode == "bilingual_to_aligned":
        result = process_bilingual_file(text1)

        alignment = result["alignment"]
        failed_lines = result["failed_lines"]

        format = request.form.get("format", "csv")

        # --- MAIN OUTPUT (CSV or TMX) ---
        if format == "tmx":
            output_text = generate_tmx(alignment)
            filename = "bilingual_alignment.tmx"
        else:
            output_text = generate_csv(alignment)
            filename = "bilingual_alignment.csv"

        # --- FAILED LINES OUTPUT ---
        failed_text = "\n".join(failed_lines)
        failed_filename = "failed_lines.txt"

        # Return BOTH files as a ZIP
        import io, zipfile
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as z:
            z.writestr(filename, output_text)
            z.writestr(failed_filename, failed_text)

        zip_buffer.seek(0)

        return Response(
            zip_buffer.getvalue(),
            mimetype="application/zip",
            headers={"Content-Disposition": "attachment; filename=bilingual_output.zip"}
        )


    else:
        return "Invalid mode", 400


if __name__ == "__main__":
    app.run(debug=True)
