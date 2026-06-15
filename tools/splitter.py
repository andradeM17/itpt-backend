import nltk
#nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

def split_sentences(text: str):
    return nltk.sent_tokenize(text)