import argparse
import logging
import os
import pathlib
import signal
import shutil
import subprocess
import time

from extraction_error import ExtractionError
from text_extractor import TextExtractor

logger = logging.getLogger(__name__)

class EditableTextExtractor(TextExtractor):

    DEFAULT_SUBPROCESS_TIMEOUT = 60
    DEFAULT_FILE_WRITE_TIMEOUT = 60

    def extract(self, input_path, output_path, config={}):
        logger.info("Extracting text from {0} to {1}.".format(input_path, output_path))

        try:
            subprocess_timeout = int(config.get("libreoffice_subprocess_timeout", self.DEFAULT_SUBPROCESS_TIMEOUT))
            file_write_timeout = int(config.get("libreoffice_file_write_timeout", self.DEFAULT_FILE_WRITE_TIMEOUT))

            output_dirname = pathlib.Path(output_path).parent
            self.start_extraction(input_path, output_dirname, subprocess_timeout)

            input_extension = pathlib.Path(input_path).suffix
            input_basename = pathlib.Path(input_path).name
            generated_filename = pathlib.Path(str(output_dirname.joinpath(input_basename)).replace(input_extension, ".txt"))
            logger.debug("Expected generated filename {0}".format(generated_filename))
            self.complete_file_writing(generated_filename, output_path, file_write_timeout)

        except Exception as e:
            logger.error("Error extracting file: {0}.".format(e))
            raise ExtractionError(e)


    def start_extraction(self, input_path, output_dirname, subprocess_timeout):
        try:
            process = subprocess.Popen([
                self.extraction_tool,
                "--convert-to", "txt",
                "--headless",
                "--outdir", output_dirname,
                input_path,
            ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, start_new_session=True)
            rc = process.wait(timeout=subprocess_timeout)
            if rc != 0:
                logger.error("Non-zero return code {0} from extraction subprocess; output file may be absent or incomplete.".format(rc))
                raise ExtractionError("Non-zero return code {0} from extraction subprocess.".format(rc))
        except subprocess.TimeoutExpired:
            logger.error("Subprocess did not complete within required {0} seconds; output file may be absent or incomplete.".format(subprocess_timeout))
            # This is necessary because libreoffice convert-to starts another process that runs in the background;
            # All subprocesses spawned by the child process must be killed along with it
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait()
            raise ExtractionError("Subprocess did not complete within required {0} seconds.".format(subprocess_timeout))


    def complete_file_writing(self, generated_filename, output_path, file_write_timeout):
        # This is necessary because there may be another instance of libreoffice running, in which case a new process would not be started
        # The file is not then guaranteed to be finished when the above subprocess returns
        previous_size = -1
        current_size = 0
        elapsed = 0
        while elapsed <= file_write_timeout and not self.file_complete(generated_filename, previous_size, current_size):
            elapsed += 1
            time.sleep(1)
            previous_size = current_size
            current_size = self.get_file_size(generated_filename)
        if elapsed >= file_write_timeout:
            message = "File writing not completed within required {0} seconds.".format(file_write_timeout)
            logger.error(message)
            raise ExtractionError(message)
        else:
            shutil.move(generated_filename, output_path)


    def get_file_size(self, filename):
        if filename.is_file():
            return filename.stat().st_size
        return 0


    def file_complete(self, filename, previous_size, current_size):
        if not filename.is_file():
            return False
        return current_size == previous_size


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("libreoffice_path", help="path to libreoffice")
    argparser.add_argument("input_path", help="path to input file")
    argparser.add_argument("output_path", help="path to output file")
    argparser.add_argument("--subprocess_timeout", type=int, default=60, help="timeout limit in seconds for running extraction subprocess")
    argparser.add_argument("--file_write_timeout", type=int, default=60, help="timeout limit in seconds for writing output file")
    args = argparser.parse_args()

    config = {
        "libreoffice_subprocess_timeout" : args.subprocess_timeout,
        "libreoffice_file_write_timeout" : args.file_write_timeout,
    }

    EditableTextExtractor(args.libreoffice_path).extract(args.input_path, args.output_path, config)
