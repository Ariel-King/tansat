# coding:utf-8
import logging
import logging.config
import sys, os

localpath = os.path.split(os.path.realpath(__file__))[0]    # 取得本程序所在目录
logging.config.fileConfig(os.path.join(localpath, "logging.conf"))

def getFuncName():
    return sys._getframe(2).f_code.co_name
        
def info(msg):
    #create logger
    logger = logging.getLogger(getFuncName())
    logger.info(msg)

def error(msg):
    #create logger
    logger = logging.getLogger(getFuncName())
    logger.error(msg)
    
if __name__=='__main__':
    def aaa():
        try:
            info('message1')
        finally:
            error('message2')
    aaa()