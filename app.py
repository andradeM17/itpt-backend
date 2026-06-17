from flask import Flask, request, send_file, jsonify, Response
from flask_cors import CORS
from tools.detector import detect_language
from tools.splitter import split_sentences
from tools.aligner import align_sentences
from tools.csv_generator import generate_csv
from tools.tmx_generator import generate_tmx
import io

app = Flask(__name__)
CORS(app)

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


# -----------------------------
# Your existing /process endpoint
# -----------------------------

@app.route("/process", methods=["POST"])
def process():
    mode = request.form.get("mode")
    format = request.form.get("format", "csv")
    file1 = request.files["file1"]
    text1 = file1.read().decode("utf-8")

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
        text2 = file2.read().decode("utf-8")

        alignment = align_sentences(text1, text2)

        if format == "tmx":
            output_text = generate_tmx(alignment)
            filename = "alignment.tmx"
        else:
            output_text = generate_csv(alignment)
            filename = "alignment.csv"

        return Response(
            output_text,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    else:
        return "Invalid mode", 400


if __name__ == "__main__":
    app.run(debug=True)
