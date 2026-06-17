import subprocess
import tempfile
import platform
import os
from nltk.translate import AlignedSent, IBMModel1
import nltk

# Path to bundled binary
if platform.system() == "Windows":
    nltk.download("punkt", quiet=True)

    def align_sentences(src_text: str, tgt_text: str):
        src_sents = nltk.sent_tokenize(src_text)
        tgt_sents = nltk.sent_tokenize(tgt_text)

        aligned = []
        for s, t in zip(src_sents, tgt_sents):
            aligned.append({"source": s, "target": t})

        return aligned
else:
    HUNALIGN_PATH = os.path.join(os.path.dirname(__file__), "hunalign", "hunalign")

    # If you have no dictionary, use /dev/null
    DICTIONARY_PATH = "/dev/null"

    def align_sentences(src_text: str, tgt_text: str):
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as src_file:
            src_file.write(src_text)
            src_path = src_file.name

        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as tgt_file:
            tgt_file.write(tgt_text)
            tgt_path = tgt_file.name

        # Run hunalign
        cmd = [HUNALIGN_PATH, DICTIONARY_PATH, src_path, tgt_path]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Clean up
        os.remove(src_path)
        os.remove(tgt_path)

        # Parse output
        alignment = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                alignment.append({
                    "source": parts[0].strip(),
                    "target": parts[1].strip()
                })

        return alignment