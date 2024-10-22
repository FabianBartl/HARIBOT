"""
created by @fabianbartl

a custom formatter for the built-in logging library to support nice colored
console output alongside logging to file with utf-8 encoding

inspired by:
 - https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging/

example config:
```
setBasicConfig(level=logging.DEBUG,
               format="%(asctime)s | %(levelname)8s | %(message)s",
               date_format="%Y-%m-%d %H:%M:%S",
               path=f"log.txt",
               use_color=True)
logger = getLogger()
```
"""

import logging
from colorama import Fore, Back, Style

# own debug log level above default debug
MY_DEBUG = 15

class CustomFormatter(logging.Formatter):
    def __init__(self, format:str, *, use_color:bool=True) -> None:
        self.debug_color    = Style.DIM
        self.info_color     = Fore.CYAN
        self.warning_color  = Fore.YELLOW
        self.error_color    = Fore.RED+Style.BRIGHT
        self.critical_color = Fore.WHITE+Back.RED
        self.reset_color    = Fore.RESET+Back.RESET+Style.RESET_ALL
        
        super().__init__()
        global MY_DEBUG
        self.fmt = format
        if use_color:
            self.FORMATS = {
                logging.DEBUG:    f"{self.debug_color}{self.fmt}{self.reset_color}",
                MY_DEBUG:         f"{self.debug_color}{self.fmt}{self.reset_color}",
                logging.INFO:     f"{self.info_color}{self.fmt}{self.reset_color}",
                logging.WARNING:  f"{self.warning_color}{self.fmt}{self.reset_color}",
                logging.ERROR:    f"{self.error_color}{self.fmt}{self.reset_color}",
                logging.CRITICAL: f"{self.critical_color}{self.fmt}{self.reset_color}"
            }
        else:
            self.FORMATS = {
                logging.DEBUG:    f"{self.fmt}",
                MY_DEBUG:         f"{self.fmt}",
                logging.INFO:     f"{self.fmt}",
                logging.WARNING:  f"{self.fmt}",
                logging.ERROR:    f"{self.fmt}",
                logging.CRITICAL: f"{self.fmt}"
            }

    def format(self, record:logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setBasicConfig(level:int, format:str, date_format:str, path:str, *, use_color:bool=True) -> None:
    # create stdout handler for logging to the console
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(CustomFormatter(format, use_color=use_color))

    # create file handler for logging to a file
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(format))

    logging.basicConfig(
        level=level,
        encoding="utf-8",
        format=format,
        datefmt=date_format,
        handlers=[file_handler, stdout_handler]
    )

def getLogger() -> logging.Logger:
    return logging.getLogger(__name__)

def debug(message:str) -> None:
    global MY_DEBUG
    getLogger().log(MY_DEBUG, message)
