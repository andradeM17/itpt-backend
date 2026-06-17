import os
import platform
import subprocess
import tempfile
from itertools import zip_longest
import nltk


if platform.system() == "Windows":
    nltk.download("punkt", quiet=True)


def sentence_split(text: str):
    return nltk.sent_tokenize(text)


def simple_alignment(src_sents, tgt_sents):
    alignment = []

    for src, tgt in zip_longest(src_sents, tgt_sents, fillvalue=""):
        alignment.append({
            "source": src,
            "target": tgt
        })

    return alignment


def hunalign_alignment(src_sents, tgt_sents):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    hunalign_path = os.path.join(base_dir, "hunalign", "hunalign")
    dictionary_path = "/dev/null"

    src_path = None
    tgt_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False
        ) as src_file:
            src_file.write("\n".join(src_sents))
            src_path = src_file.name

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False
        ) as tgt_file:
            tgt_file.write("\n".join(tgt_sents))
            tgt_path = tgt_file.name

        result = subprocess.run(
            [hunalign_path, dictionary_path, src_path, tgt_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Hunalign failed (exit code {result.returncode})\n"
                f"{result.stderr}"
            )

        alignment = []

        for line in result.stdout.splitlines():
            parts = line.strip().split("\t")

            if len(parts) < 2:
                continue

            try:
                src_idx = int(parts[0])
                tgt_idx = int(parts[1])

                alignment.append({
                    "source": src_sents[src_idx] if 0 <= src_idx < len(src_sents) else "",
                    "target": tgt_sents[tgt_idx] if 0 <= tgt_idx < len(tgt_sents) else ""
                })

            except ValueError:
                continue

        return alignment

    finally:
        if src_path and os.path.exists(src_path):
            os.remove(src_path)

        if tgt_path and os.path.exists(tgt_path):
            os.remove(tgt_path)


def align_sentences(src_text: str, tgt_text: str):
    src_sents = sentence_split(src_text)
    tgt_sents = sentence_split(tgt_text)

    if platform.system() == "Windows":
        return simple_alignment(src_sents, tgt_sents)

    return hunalign_alignment(src_sents, tgt_sents)