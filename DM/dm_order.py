# coding=UTF-8
from time import sleep
__author__ = 'wangpeng'

import os, sys, re, log
from datetime import date, timedelta
from configobj import ConfigObj
from posixpath import join as urljoin
import ftplib, ftputil
import urllib, urllib2
from HTMLParser import HTMLParser


def main(Cfg):
    #获取参数
    xArg = sys.argv[1:]
    args_nums = len(xArg)
    if args_nums != 2:
        print "Wrong Input!"
        return

    #获取处理文件时间和文件类型
    Ftime = xArg[0]
    Ftype = xArg[1]

    #获取FTP信息
    HOST = Cfg[Ftype]['HOST']
    PORT = Cfg[Ftype]['PORT']
    USER = Cfg[Ftype]['USER']
    PAWD = Cfg[Ftype]['PAWD']
    SDIR = Cfg[Ftype]['SDIR']
    SDIR_IS_PATH = Cfg[Ftype]['SDIR_IS_PATH']

    #获取目录信息
    ORDER_DIR = Cfg['DIR']['ORDER']
    LOG = Cfg['DIR']['LOG']


    #获取日志文件的路径
    LOG_DIR = os.path.split(LOG)[0]
    #日志目录不存在创建
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    #正确的日期格式正则
    patRange = '(\d{8})-(\d{8})'

    if len(xArg[0]) == 17:
        m = re.match(patRange, xArg[0])
        if m is None:
            print 'Wrong Input!'
            return
        ymd1 = m.group(1)
        ymd2 = m.group(2)
        date1 = date(int(ymd1[0:4]), int(ymd1[4:6]), int(ymd1[6:8]))
        date2 = date(int(ymd2[0:4]), int(ymd2[4:6]), int(ymd2[6:8]))
        print date1, date2
        #时间循环
        while date1 <= date2:
            Ymd = date1.strftime('%Y%m%d')
            RegYmd = date1.strftime('%d%b%Y')
            date1 = date1 + timedelta(days=1)

            #要下载的FTP的目录循环
            for DIR in SDIR:
                #替换字符中的YYYYMMDD为当前输入时间
                DIR = DIR.replace('%YYYY', Ymd[0:4])
                DIR = DIR.replace('%MM', Ymd[4:6])
                DIR = DIR.replace('%DD', Ymd[6:8])

                # 拼接本地存储目录 和 订单文件
                if SDIR_IS_PATH.strip() == 'yes':
                    FULL_ORDER_DIR = urljoin(ORDER_DIR, Ftype, DIR)
                elif SDIR_IS_PATH.strip() == 'no':
                    FULL_ORDER_DIR = urljoin(ORDER_DIR, Ftype)


                if not os.path.exists(FULL_ORDER_DIR):
                    os.makedirs(FULL_ORDER_DIR)

                URL = dm_oder_ftp_unit(HOST, USER, PAWD, PORT, DIR, RegYmd)

                ORDER_FILE = urljoin(FULL_ORDER_DIR, Ymd + '.txt')

                if URL != []:
                    if not os.path.isfile(ORDER_FILE):
                        fp = open(ORDER_FILE, 'w')
                        fp.writelines(URL)
                        fp.close()
                        log.info("%s %s order success" % (Ymd, DIR))
                    else:
                        log.info("%s %s order exists" % (Ymd, DIR))
                else:
                    print "Blank URL in %s %s" % (Ymd, DIR)


def dm_oder_ftp_unit(HOST, USER, PAWD, PORT, SDIR, REG):
    '''

    :param HOST: 主机地址
    :param USER: 用户
    :param PAWD: 密码
    :param PORT: 端口
    :param FTP_DIR: FTP上的目录
    :param REG: 匹配规则，需要从FTP上面查找什么时间的文件
    :return:
    '''
    URL = []

    class MySession(ftplib.FTP):
        def __init__(self, FTP, userid, password, port):
            """Act like ftplib.FTP's constructor but connect to another port."""
            ftplib.FTP.__init__(self)
            self.connect(FTP, port)
            self.login(userid, password)

    with ftputil.FTPHost(HOST, USER, PAWD, port=PORT, session_factory=MySession) as FTP:
#         print "SDIR(FTP_DIR): ", SDIR

        filelst = FTP.listdir(SDIR)
#         print "filelst: ", filelst
#         print "SDIR: ", SDIR
        for eachfile in filelst:
            full_name = FTP.path.join(SDIR, eachfile)
            if FTP.path.isdir(full_name):
                continue
            else:
                if REG in eachfile:
                    stat = FTP.lstat(full_name)
                    size = stat[6]
                    url = 'ftp://' + HOST + ':' + PORT + '/' + full_name + ' ' + str(size) + '\n'
                    print url
                    URL.append(url)

    return URL


if __name__ == '__main__':
    '''
    获取程序同名的配置文件
    '''
    MainPath, MainFile = os.path.split(os.path.realpath(__file__))
    # MainCfg = urljoin(MainPath, MainFile.split('.')[0]+'.cfg')
    MainCfg = urljoin(MainPath, 'dm.cfg')
    Cfg = ConfigObj(MainCfg)
    print 'use config: ', MainCfg
    main(Cfg)


