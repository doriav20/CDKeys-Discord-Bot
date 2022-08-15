import logging
import logging.handlers

_250MB_IN_BYTES = 250 * 1024 * 1024
configured = False


def config_logger():
    rotating_file_handler = logging.handlers.RotatingFileHandler(
        filename='log.log',
        mode='a',
        maxBytes=_250MB_IN_BYTES,
        backupCount=1,
        encoding=None,
        delay=0
    )
    format = '%(levelname)s | File "%(filename)s", line %(lineno)s, in %(funcName)s | %(asctime)s - %(message)s'
    logging.basicConfig(
        format=format,
        level=logging.DEBUG,
        handlers=[rotating_file_handler],
    )
    global configured
    configured = True


def get_logger(name):
    if not configured:
        config_logger()
    return logging.getLogger(name)
