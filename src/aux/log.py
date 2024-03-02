import logging
import __main__


LOGFILE = True

#formatters
simple_formatter = logging.Formatter("%(name)-25s - %(message)s")
#handlers
console = logging.StreamHandler()

if 'exam' in __main__.__file__:
    file_handler = logging.FileHandler(filename="checks_log.txt", delay=True)
else:
    file_handler = logging.FileHandler(filename="build_log.txt", delay=True)
#config
console.setLevel(logging.ERROR)
console.setFormatter(simple_formatter)

file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(simple_formatter)
#loggers
console_logger = logging.getLogger('console_logger')
checks_logger = logging.getLogger('Checks')
#configs
console_logger.addHandler(console)

checks_logger.addHandler(console)
checks_logger.setLevel(logging.DEBUG)
checks_logger.addHandler(file_handler)


def remove_filehandler():
    global LOGFILE
    for logger in logging.Logger.manager.loggerDict.values():
        logger.removeHandler(file_handler)
    LOGFILE = False

def set_log_level(level):
    for logger in logging.Logger.manager.loggerDict.values():
        if len(logger.handlers) < 2: continue
        try:
            var = eval(f'logging.{level[0]}')
            eval("logger.handlers[1].setLevel(var)")
        except:
            raise ValueError(f'Invalid log level: {level}')

def get_new_logger(name):
    global LOGFILE
    global file_handler
    logger = logging.getLogger(name)
    logger.addHandler(console)
    if LOGFILE:
        logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    return logger
