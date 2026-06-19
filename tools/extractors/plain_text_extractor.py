import logging
import shutil

from tools.extractors.extraction_error import ExtractionError
from tools.extractors.text_extractor import TextExtractor

logger = logging.getLogger(__name__)

class PlainTextExtractor(TextExtractor):

    def extract(self, input_path, output_path, config={}):
        logger.info("Copying plaintext from {0} to {1}.".format(input_path, output_path))
        try:
            shutil.copyfile(input_path, output_path)
        except Exception as e:
            logger.error("Error extracting file: {0}.".format(e))
            raise ExtractionError(e)
