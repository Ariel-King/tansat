# coding=UTF-8
__author__ = 'wangpeng'
 
import os, sys, re, time, log
from datetime import datetime, timedelta
from configobj import ConfigObj
from posixpath import join as urljoin
import ftplib, ftputil
import urllib, urllib2
from HTMLParser import HTMLParser
from multiprocessing import Pool
import subprocess


MainPath, MainFile = os.path.split(os.path.realpath(__file__))
# MainCfg = os.path.join(MainPath, MainFile.split('.')[0]+'.cfg')
MainCfg = os.path.join(MainPath, 'dm.cfg')
Cfg = ConfigObj(MainCfg)


def main():
    # 获取参数
    xArg = sys.argv[1:]

    # 参数个数目前为2个
    args_nums = len(xArg)
    if args_nums != 2:
        print 'input error: args nums is two!'
        return

    # 获取处理文件时间和文件类型
    Ftime = xArg[0]
    Ftype = xArg[1]

    ORDER_DIR = Cfg['DIR']['ORDER']
    TDATA_DIR = Cfg['DIR']['TDATA']

    SERVER_DIR = Cfg[Ftype]['SDIR']
    SDIR_IS_PATH = Cfg[Ftype]['SDIR_IS_PATH']
    THRED = Cfg['WGET']['THRED']

    for DIR in SERVER_DIR:
        ALL_LINES = []
        #从时间参数上获取开始时间和结束时间
        date_s, date_e = ymd2date(Ftime)

        # 拼接本地存储目录 和 订单文件
        if SDIR_IS_PATH.strip() == 'yes':
            LOCAL_DIR = urljoin(TDATA_DIR, Ftype, DIR)
            FULL_ORDER_DIR = urljoin(ORDER_DIR, Ftype, DIR)
        elif SDIR_IS_PATH.strip() == 'no':
            LOCAL_DIR = urljoin(TDATA_DIR, Ftype)
            FULL_ORDER_DIR = urljoin(ORDER_DIR, Ftype)
        while date_s <= date_e:
            Ymd = date_s.strftime('%Y%m%d')
            date_s = date_s + timedelta(days=1)
            ORDER_FILE = urljoin(FULL_ORDER_DIR, Ymd + '.txt')
            print ORDER_FILE

            # 创建本地存储目录
            if not os.path.exists(LOCAL_DIR):
                os.makedirs(LOCAL_DIR)
            # 如果订单文件存在，则进行解析下载
            if os.path.isfile(ORDER_FILE):
                #读取订单文件
                fp = open(ORDER_FILE, 'r')
                LINES = fp.readlines()
                fp.close()
                ALL_LINES = ALL_LINES + LINES
        #
        RealNums = len(ALL_LINES)
        log.info(u'Download %s %s %s' % (Ftype, DIR, RealNums))
        # 实例化下载类
        dm = DM()
        dm.Ftype = Ftype
        #dm.Ymd = Ymd
        dm.LOCAL_DIR = LOCAL_DIR

        # 支持多线程下载
        pool = Pool(processes=int(THRED))
        pool.map(dm, ALL_LINES)

def ymd2date(Ftime):
    # 正确的日期格式正则
    patRange = '(\d{8})-(\d{8})'
    if len(Ftime) == 17:
        m = re.match(patRange, Ftime)
        if m is None:
            print 'please input time: YYYYMMDD-YYYYMMDD!'
            return
        else:
            ymd1 = m.group(1)
            ymd2 = m.group(2)
            date_s = datetime(int(ymd1[0:4]), int(ymd1[4:6]), int(ymd1[6:8]))
            date_e = datetime(int(ymd2[0:4]), int(ymd2[4:6]), int(ymd2[6:8]))
            return date_s, date_e
    else:
        print 'time format error'
        return

class DM():
    def __init__(self):

        self.Ftype = ''
        #self.Ymd = ''
        self.LOCAL_DIR = ''

    def __call__(self, line):
        self.download(line)

    def download(self, line):

        # 获取配置文件相关信息
        USER = Cfg[self.Ftype]['USER']
        PAWD = Cfg[self.Ftype]['PAWD']

        # 获取WGET参数信息
        WGET = Cfg['WGET']['BIN']
        TRIES = Cfg['WGET']['TRIES']
        TIMEOUT = Cfg['WGET']['TIMEOUT']
        WAIT = Cfg['WGET']['WAIT']
        WAITRETRY = Cfg['WGET']['WAITRETRY']
        RANDOM = Cfg['WGET']['RANDOM']
        LIMIT_RATE = Cfg['WGET']['LIMIT_RATE']

        # 在订单中获取下载地址和数据大小
        ServerUrl = line.split()[0]
        ServerSize = line.split()[1]
        FileName = os.path.split(ServerUrl)[1]
        LocalFile = urljoin(self.LOCAL_DIR, FileName)
        TmpLocalFile = LocalFile + '.lock'
        print WGET

        if not os.path.isfile(WGET):
            log.info(u'wget.exe not found')
            return


        # 封装WGET命令参数
        cmd = '''%s --user=%s --password=%s --tries=%s --timeout=%s \
                    --waitretry=%s --random-wait=%s --wait=%s --limit-rate=%s \
                    -c -q --no-parent -nd -nH  \
                    --directory-prefix=%s %s''' \
              % ( WGET, USER, PAWD, TRIES, TIMEOUT,
                  WAITRETRY, RANDOM, WAIT, LIMIT_RATE,
                  self.LOCAL_DIR, ServerUrl )

        # 第一次获取本地文件大小
        if not os.path.isfile(LocalFile):
            LocalSize = 0
        else:
            LocalSize = os.path.getsize(LocalFile)


        # 如果本地文件不完整，则继续下载, 并创建同命的.lock文件

        if ( float(LocalSize) < float(ServerSize)):
            if not os.path.isfile(TmpLocalFile):
                fp = open(TmpLocalFile, 'w')
                fp.close()
            #retcode = subprocess.call(cmd, shell=True)
            os.system(cmd)

        # 下载结束后，第二次获取本地文件大小，
        if not os.path.isfile(LocalFile):
            LocalSize = 0
        else:
            LocalSize = os.path.getsize(LocalFile)

        # 如果文件大小为0则删除临时文件
        if ( LocalSize == 0 ):
            if os.path.isfile(TmpLocalFile):
                os.unlink(TmpLocalFile)

        # 下载完成后，删除临时文件
        if (float(LocalSize) >= float(ServerSize)):
            # print FileName, LocalSize, ServerSize
            if os.path.isfile(TmpLocalFile):
                os.unlink(TmpLocalFile)
        # else:
        #     print FileName, LocalSize, ServerSize

        return 0


if __name__ == '__main__':

    print u'use：', MainCfg
    # 获取日志文件的路径
    LOG_FILE = Cfg['DIR']['LOG']
    LOG_DIR, LOG_FILE = os.path.split(LOG_FILE)
    # 日志目录不存在创建
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    main()
