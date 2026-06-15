from flask import Flask, request, send_file
from flask_cors import CORS
from tools.detector import detect_language
from tools.splitter import split_sentences
from tools.aligner import align_sentences
import io

app = Flask(__name__)
CORS(app)

@app.route("/process", methods=["POST"])
def process():
    mode = request.form.get("mode")
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

        lines = []
        for pair in alignment:
            lines.append(f"SRC: {pair['source']}")
            lines.append(f"TGT: {pair['target']}")
            lines.append("")

        output = "\n".join(lines)

        return send_file(
            io.BytesIO(output.encode("utf-8")),
            as_attachment=True,
            download_name="alignment.txt",
            mimetype="text/plain"
        )

    else:
        return "Invalid mode", 400


if __name__ == "__main__":
    app.run(debug=True)
