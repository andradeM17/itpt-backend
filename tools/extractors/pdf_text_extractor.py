import argparse
import logging
import subprocess

from toolchain.extractors.extraction_error import ExtractionError
from toolchain.extractors.text_extractor import TextExtractor

logger = logging.getLogger(__name__)

class PdfTextExtractor(TextExtractor):

    DEFAULT_SUBPROCESS_TIMEOUT = 120

    def extract(self, input_path, output_path, config={}):
        logger.info("Extracting text from {0} to {1}.".format(input_path, output_path))
        subprocess_timeout = int(config.get("pdftotext_subprocess_timeout", self.DEFAULT_SUBPROCESS_TIMEOUT))
        try:
            result = subprocess.run([
                self.extraction_tool,
                input_path, output_path,
            ], timeout=subprocess_timeout, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            rc = result.returncode
            if rc != 0:
                logger.error("Non-zero return code {0} from extraction subprocess; output file may be absent or incomplete.".format(rc))
                raise ExtractionError("Non-zero return code {0} from extraction subprocess.".format(rc))
        except subprocess.TimeoutExpired:
            logger.error("Subprocess did not complete within required {0} seconds; output file may be absent or incomplete.".format(subprocess_timeout))
            raise ExtractionError("Subprocess did not complete within required {0} seconds.".format(subprocess_timeout))
        except Exception as e:
            logger.error("Error extracting file: {0}.".format(e))
            raise ExtractionError(e)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("pdftotext_path", help="path to pdftotext")
    argparser.add_argument("input_path", help="path to input file")
    argparser.add_argument("output_path", help="path to output file")
    argparser.add_argument("--subprocess_timeout", type=int, default=120, help="timeout limit in seconds for running extraction subprocess")
    args = argparser.parse_args()

    config = {
        "pdftotext_subprocess_timeout" : args.subprocess_timeout,
    }

    PdfTextExtractor(args.pdftotext_path).extract(args.input_path, args.output_path, config)
