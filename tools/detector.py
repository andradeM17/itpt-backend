from tools.langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    print("[LANGDETECT] Received text length:", len(text))
    print("[LANGDETECT] First 200 chars:", repr(text[:200]))
    return detect(text)