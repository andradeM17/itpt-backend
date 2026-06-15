from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    return detect(text)