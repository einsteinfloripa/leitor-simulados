import logging


#formatters
simple_formatter = logging.Formatter("%(name)-25s - %(message)s")
#handlers
console = logging.StreamHandler()

file_handler = logging.FileHandler(filename="checks_log.txt", delay=True)
#config
console.setLevel(logging.WARNING)
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
    for logger in logging.Logger.manager.loggerDict.values():
        logger.removeHandler(file_handler)
    # checks_logger.removeHandler(file_handler)

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
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    return logger
