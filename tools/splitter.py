import nltk
#nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

def split_sentences(text: str):
    chunks = text.split("\r\n")
    sentences = []

    for chunk in chunks:
        sentences.extend(nltk.sent_tokenize(chunk))

    for i, sentence in enumerate(sentences):
        print("[SPLITTER] Sentence", i, "length:", len(sentence))

    return sentences