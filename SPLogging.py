# Copyright (c) 2010 stas zytkiewicz stas@childsplay.mobi
#


# provides a logging object
# All modules get the same logger so this must called asap

__author__ = 'stas'
import logging

# Added custom loglevel as various parts of kivy also using it
import time

logging.TRACE = logging.INFO + 5
logging.addLevelName(logging.INFO + 5, 'TRACE')

import logging.handlers
import os
from copy import copy

LOGDIR = '/data/userdata/.schoolsplay.rc/logs'
if not os.path.exists(LOGDIR):
    os.makedirs(LOGDIR)
LOGPATH = os.path.join(LOGDIR, 'NMKivy.log')

use_color =True

# Color logging taken from the kivy logger
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = list(range(8))

# These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

COLORS = {
    'TRACE': YELLOW,
    'WARNING': MAGENTA,
    'INFO': BLUE,
    'DEBUG': CYAN,
    'CRITICAL': RED,
    'ERROR': RED}

class ColoredFormatter(logging.Formatter):

    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        col_record = copy(record)
        levelname = col_record.levelname
        if col_record.levelno == logging.TRACE:
            levelname = 'TRACE'
            col_record.levelname = levelname
        if self.use_color and levelname in COLORS:
            levelname_color = (
                COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ)
            col_record.levelname = levelname_color
        return logging.Formatter.format(self, col_record)

class DuplicateFilter(logging.Filter):

    def filter(self, record):
        # add other fields if you need more granular comparison, depends on your app
        current_log = (record.levelname, record.lineno, record.msg)
        if current_log != getattr(self, "last_log", None):
            self.last_log = current_log
            return True
        return False

# set loglevel, possible values:
# logging.DEBUG
# logging.INFO
# logging.WARNING
# logging.ERROR
# logging.CRITICAL

def set_level(level):
    global CONSOLELOGLEVEL, FILELOGLEVEL
    lleveldict = {'debug': logging.DEBUG,
                  'info': logging.INFO,
                  'warning': logging.WARNING,
                  'error': logging.ERROR,
                  'critical': logging.CRITICAL}
    if level not in lleveldict:
        print(("Invalid loglevel: %s, setting loglevel to 'debug'" % level))
        llevel = lleveldict['debug']
    else:
        llevel = lleveldict[level]
    CONSOLELOGLEVEL = llevel
    FILELOGLEVEL = llevel


def start():
    global CONSOLELOGLEVEL, FILELOGLEVEL
    # create logger
    logger = logging.getLogger("sp")
    logger.addFilter(DuplicateFilter())
    logger.setLevel(CONSOLELOGLEVEL)

    # create console handler and set level
    ch = logging.StreamHandler()
    ch.setLevel(CONSOLELOGLEVEL)

    # create rotating file handler and set level
    fh = logging.handlers.RotatingFileHandler(LOGPATH, maxBytes=1024 * 1024 * 1, backupCount=2)
    # fh = logging.FileHandler(LOGPATH, encoding='utf8')
    fh.setLevel(FILELOGLEVEL)

    # create formatter
    msg = u"[%(levelname)-7s] - %(asctime)s - %(name)s:%(lineno)d > %(message)s"
    color_msg = u"[%(levelname)-7s] - %(asctime)s - %(name)s:%(lineno)d > %(message)s"

    # add formatter to ch and fh
    ch.setFormatter(ColoredFormatter(color_msg, use_color=use_color))
    fh.setFormatter(logging.Formatter(msg))

    # add ch and fh to logger
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.info("logger created: %s" % LOGPATH)

    # test
    module_logger = logging.getLogger("sp.SPLogging")
    module_logger.info("******************************")
    module_logger.info(f"** {time.asctime()} **")
    module_logger.info("******************************")
    module_logger.info(f"logger created, start logging to {LOGPATH}")
