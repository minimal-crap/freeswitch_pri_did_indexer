import logging
import os

from components.conf import settings


class Logger:

    def __init__(self,
                 file_name=None,
                 log_dir=None,
                 stream_handler=None,
                 file_handler=None
                 ):
        try:
            if file_name is None:
                raise Exception("log file name not defined")

            if log_dir is None:
                self.log_dir = settings.LOG_DIR
            else:
                self.log_dir = log_dir

            self.logger = logging.getLogger(name=file_name)
            log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.logger.setLevel(logging.DEBUG)

            if file_handler:
                self.file_handler = logging.FileHandler(os.path.join(self.log_dir, file_name))
                self.file_handler.setFormatter(log_format)
                self.file_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(self.file_handler)
            if stream_handler:
                self.stream_handler = logging.StreamHandler()
                self.stream_handler.setFormatter(log_format)
                self.stream_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(self.stream_handler)

        except Exception as err:
            print err.message + "logger::init"
