import os
from langdetect import DetectorFactory, detector_factory

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "custom_profiles")

detector_factory.load_profiles(PROFILE_DIR)
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    detector = detector_factory.create()
    detector.append(text)
    return detector.detect()
