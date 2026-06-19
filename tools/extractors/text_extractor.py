from abc import ABC, abstractmethod

class TextExtractor(ABC):

    def __init__(self, extraction_tool):
        self.extraction_tool = extraction_tool

    @abstractmethod
    def extract(self, input_path, output_path, config={}):
        pass
