from nltk.translate import AlignedSent, IBMModel1
import nltk

nltk.download("punkt", quiet=True)

def align_sentences(src_text: str, tgt_text: str):
    src_sents = nltk.sent_tokenize(src_text)
    tgt_sents = nltk.sent_tokenize(tgt_text)

    aligned = []
    for s, t in zip(src_sents, tgt_sents):
        aligned.append({"source": s, "target": t})

    return aligned
