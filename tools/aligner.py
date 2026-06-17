import os
import platform
import subprocess
import tempfile
from itertools import zip_longest
from tools.splitter import split_sentences


def simple_alignment(src_sents, tgt_sents):
    alignment = []
    for src, tgt in zip_longest(src_sents, tgt_sents, fillvalue=""):
        alignment.append({
            "source": src,
            "target": tgt
        })
    return alignment


def hunalign_alignment(src_sents, tgt_sents):
    # Absolute path to the static binary
    base_dir = os.path.dirname(os.path.abspath(__file__))
    hunalign_path = os.path.join(base_dir, "hunalign", "hunalign")

    dictionary_path = "/dev/null"

    # Write full sentence lists ONCE to /tmp
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, dir="/tmp") as src_file:
        src_file.write("\n".join(src_sents))
        src_path = src_file.name

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, dir="/tmp") as tgt_file:
        tgt_file.write("\n".join(tgt_sents))
        tgt_path = tgt_file.name

    try:
        # Call hunalign ONCE
        result = subprocess.run(
            [hunalign_path, dictionary_path, src_path, tgt_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        # If hunalign fails, fall back to simple alignment
        if result.returncode != 0:
            return simple_alignment(src_sents, tgt_sents)

        alignment = []

        # Parse hunalign output
        for line in result.stdout.splitlines():
            parts = line.strip().split("\t")

            # Expect: src_idx \t tgt_idx \t score
            if len(parts) < 2:
                continue

            try:
                src_idx = int(parts[0])
                tgt_idx = int(parts[1])
            except ValueError:
                continue

            # Skip dummy 0→0 fallback
            #if src_idx == 0 and tgt_idx == 0:
            #    continue

            alignment.append({
                "source": src_sents[src_idx] if 0 <= src_idx < len(src_sents) else "",
                "target": tgt_sents[tgt_idx] if 0 <= tgt_idx < len(tgt_sents) else ""
            })

        return alignment

    finally:
        # Cleanup
        if os.path.exists(src_path):
            os.remove(src_path)
        if os.path.exists(tgt_path):
            os.remove(tgt_path)


def align_sentences(src_text: str, tgt_text: str):
    src_sents = split_sentences(src_text)
    tgt_sents = split_sentences(tgt_text)

    if platform.system() == "Windows":
        return simple_alignment(src_sents, tgt_sents)

    return hunalign_alignment(src_sents, tgt_sents)
