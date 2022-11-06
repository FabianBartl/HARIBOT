
import logging
from colorama import Fore, Back, Style

#---------------#
# custom logger #
#---------------#

# https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging/
# https://stackoverflow.com/a/56944256/3638629

class CustomFormatter(logging.Formatter):
    def __init__(self, fmt: str, colored: bool):
        self.debug_color    = Style.DIM
        self.info_color     = Fore.BLUE
        self.warning_color  = Fore.YELLOW
        self.error_color    = Fore.RED+Style.BRIGHT
        self.critical_color = Fore.WHITE+Back.RED
        self.reset_color    = Fore.RESET+Back.RESET+Style.RESET_ALL
		
        super().__init__()
        self.fmt = fmt
        if colored:
            self.FORMATS = {
                logging.DEBUG:      f"{self.debug_color}{self.fmt}{self.reset_color}"
                , logging.INFO:     f"{self.info_color}{self.fmt}{self.reset_color}"
                , logging.WARNING:  f"{self.warning_color}{self.fmt}{self.reset_color}"
                , logging.ERROR:    f"{self.error_color}{self.fmt}{self.reset_color}"
                , logging.CRITICAL: f"{self.critical_color}{self.fmt}{self.reset_color}"
            }
        else:
            self.FORMATS = {logging.DEBUG: f"{self.fmt}", logging.INFO: f"{self.fmt}", logging.WARNING: f"{self.fmt}", logging.ERROR: f"{self.fmt}", logging.CRITICAL: f"{self.fmt}"}

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setBasicConfig(level: int, fmt: str, date_fmt: str, path: str, colored: bool):
    # Create stdout handler for logging to the console
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(CustomFormatter(fmt, colored))

    # Create file handler for logging to a file
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(fmt))

    logging.basicConfig(
        level = level
        , encoding = "utf-8"
        , format = fmt
        , datefmt = date_fmt
        , handlers = [file_handler, stdout_handler]
    )

def getLogger(init: bool=False, **kwargs):
    if init: setBasicConfig(**kwargs)
    return logging.getLogger(__name__)
