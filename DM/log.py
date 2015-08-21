import os
import logging.config
import logging
import sys
# localpath = os.path.split(os.path.realpath(__file__))[0]
# logging.config.fileConfig(os.path.join(localpath, "logging.conf"))

MainPath,MainFile = os.path.split(os.path.realpath(__file__))
MainCfg = os.path.join(MainPath, MainFile.split('.')[0]+'.cfg')
logging.config.fileConfig(MainCfg)

def getFuncName():
    return sys._getframe(2).f_code.co_name
        
def info(msg):
    #create logger

    logger = logging.getLogger(getFuncName())
    logger.info(msg)
def debug(msg):
    logger = logging.getLogger(getFuncName())
    logger.debug(msg)
def error(msg):
    #create logger
    logger = logging.getLogger(getFuncName())
    logger.error(msg)
def warning(msg):
    logger = logging.getLogger(getFuncName())
    logger.warning(msg)
if __name__=='__main__':
    def aaa():
        try:
            info('message1')
        finally:
            error('message2')
    aaa()