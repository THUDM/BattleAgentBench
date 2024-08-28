import logging

class Logger(object):
    def __init__(self, filename, fmt='%(asctime)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        self.logger.setLevel(logging.INFO)
        format_str = logging.Formatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(format_str)
        th = logging.FileHandler(filename=filename, encoding='utf-8')
        th.setFormatter(format_str)
        self.logger.addHandler(sh)
        self.logger.addHandler(th)
