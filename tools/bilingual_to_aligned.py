from tools.splitter import split_sentences
from tools.detector import detect_language
from tools.aligner import align_sentences
from tools.langdetect import LangDetectException

def process_bilingual_file(text):
    """
    Takes a single file containing two languages (Hard-coded as English and Irish) mixed line-by-line.
    Splits into sentences, detects language, groups by language,
    and aligns the two language streams.
    """

    # 1. Sentence split
    sentences = text.splitlines()

    # 2. Language detect each sentence
    EN_lines = []
    GA_lines = []
    other_lines = []

    for line in sentences:
        try:
            lang = detect_language(line)
            if lang == "en":
                EN_lines.append(line)
            elif lang == "ga":
                GA_lines.append(line)
            else:
                EN_lines.append(line)
                GA_lines.append(line)
        except LangDetectException:
            if line.strip():
                other_lines.append(line)


  
    # 3. Align using your existing aligner
    alignment = align_sentences(
        "\n".join(EN_lines),
        "\n".join(GA_lines)
    )

    return {
        "alignment": alignment,
        "failed_lines": other_lines
    }
