import logging
import os

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')


def _logger(name="default"):
    '''
    Setup logger format, level, and handler.

    RETURNS: log object
    '''
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log = logging.getLogger(name)
    log.setLevel(LOG_LEVEL)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    log.addHandler(stream_handler)
    return log
