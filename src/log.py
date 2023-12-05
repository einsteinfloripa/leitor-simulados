import logging
from logging.config import dictConfig

#formatters
simple_formatter = logging.Formatter("%(message)s")
#handlers
console = logging.StreamHandler()
#config
console.setLevel(logging.INFO)
console.setFormatter(simple_formatter)
#loggers
console_logger = logging.getLogger('console_logger')
checks_logger = logging.getLogger('checks_logger')
#configs
console_logger.addHandler(console)
checks_logger.addHandler(console)
checks_logger.setLevel(logging.DEBUG)

def enable_file_logging():
    file = logging.FileHandler(filename="debug_checks_log.txt")
    file.setLevel(logging.DEBUG)
    file.setFormatter(simple_formatter)
    checks_logger.addHandler(file)
