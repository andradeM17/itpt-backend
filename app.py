from flask import Flask, request, send_file, jsonify, Response
from flask_cors import CORS
from tools.detector import detect_language
from tools.splitter import split_sentences
from tools.aligner import align_sentences
from tools.csv_generator import generate_csv
from tools.tmx_generator import generate_tmx
from tools.bilingual_to_aligned import process_bilingual_file
import io, zipfile
import tempfile
import subprocess
import os
import logging
import docx2txt
import fitz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
CORS(app)

def extract_text_from_uploaded_file(file_storage):
    ext = file_storage.filename.lower().split(".")[-1]

    logger.info(
        f"[EXTRACTOR] Uploaded file: {file_storage.filename}, ext={ext}"
    )

    file_storage.stream.seek(0)
    raw_bytes = file_storage.stream.read()

    logger.info(
        f"[EXTRACTOR] Raw bytes length: {len(raw_bytes)}"
    )

    if not raw_bytes:
        return ""

    # TXT and other text files
    if ext not in ["doc", "docx", "pdf"]:
        try:
            text = raw_bytes.decode("utf-8")
            logger.info(
                f"[EXTRACTOR] Plain text length: {len(text)}"
            )
            return text
        except UnicodeDecodeError:
            try:
                return raw_bytes.decode("utf-8-sig")
            except Exception:
                return raw_bytes.decode(
                    "latin-1",
                    errors="ignore"
                )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{ext}"
        ) as tmp:
            tmp.write(raw_bytes)
            temp_path = tmp.name

        logger.info(
            f"[EXTRACTOR] Temporary file: {temp_path}"
        )

        # DOCX
        if ext == "docx":
            text = docx2txt.process(temp_path)

        # PDF
        elif ext == "pdf":
            doc = fitz.open(temp_path)
            text = ""
            for page in doc:
                text += page.get_text().replace("\n", "")


        logger.info(
            f"[EXTRACTOR] Extracted text length: {len(text)}"
        )

        return text

    except Exception as e:
        logger.exception(
            f"[EXTRACTOR] Extraction failed: {e}"
        )
        return ""

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


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
        files = request.files.getlist("file1")
        format = request.form.get("format", "csv")

        master_zip_buffer = io.BytesIO()

        with zipfile.ZipFile(master_zip_buffer, "w") as master_zip:

            for f in files:
                logger.info(f"[BATCH] Processing file: {f.filename}")

                text = extract_text_from_uploaded_file(f)
                result = process_bilingual_file(text)

                alignment = result["alignment"]
                failed_lines = result["failed_lines"]

                # --- MAIN OUTPUT (CSV or TMX) ---
                if format == "tmx":
                    output_text = generate_tmx(alignment)
                    main_filename = "bilingual_alignment.tmx"
                else:
                    output_text = generate_csv(alignment)
                    main_filename = "bilingual_alignment.csv"

                failed_text = "\n".join(failed_lines)

                # Add outputs directly to master ZIP (no nested ZIPs)
                safe_name = os.path.splitext(f.filename)[0]

                master_zip.writestr(f"{safe_name}_alignment.{ 'tmx' if format=='tmx' else 'csv' }", output_text)
                master_zip.writestr(f"{safe_name}_failed_lines.txt", failed_text)

        master_zip_buffer.seek(0)

        return Response(
            master_zip_buffer.getvalue(),
            mimetype="application/zip",
            headers={"Content-Disposition": "attachment; filename=batch_output.zip"}
        )


    else:
        return "Invalid mode", 400


if __name__ == "__main__":
    app.run(debug=True)
