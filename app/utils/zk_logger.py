import logging
import warnings


class ZkLogger:
    def __init__(self, color, level):
        self.min_log_level = self._get_min_log_level(level)
        self.add_colors = color

    def _get_min_log_level(self, level):
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARN": logging.WARN,
            "ERROR": logging.ERROR,
            "FATAL": logging.CRITICAL,
        }
        return level_map.get(level, logging.DEBUG)

    def _log(self, level, tag, message, *args):
        if level >= self.min_log_level:
            log_message = f"[{level}] {tag} | {message}"
            if self.add_colors:
                log_message = f"\033[0m{log_message}\033[0m"
            logging.log(level, log_message, *args)

    def debug(self, tag, message, *args):
        self._log(logging.DEBUG, tag, message, *args)

    def info(self, tag, message, *args):
        self._log(logging.INFO, tag, message, *args)

    def warn(self, tag, message, *args):
        warnings.warn(message)
        self._log(logging.WARN, tag, message, *args)

    def error(self, tag, message, *args):
        self._log(logging.ERROR, tag, message, *args)

    def fatal(self, tag, message, *args):
        self._log(logging.CRITICAL, tag, message, *args)


# fetch from config map
log_color = True
log_level = 'DEBUG'

logger = ZkLogger(log_color, log_level)


