# coding=UTF-8
__author__ = 'wangpeng'

import os, sys, re, time,log
from datetime import datetime, timedelta
from configobj import ConfigObj
from posixpath import join as urljoin
from dateutil.relativedelta import relativedelta
import urllib, urllib2
from HTMLParser import HTMLParser

'''
获取程序同名的配置文件
'''
MainPath, MainFile = os.path.split(os.path.realpath(__file__))
# MainCfg = os.path.join(MainPath, MainFile.split('.')[0]+'.cfg')
MainCfg = urljoin(MainPath, 'dm.cfg')
Cfg = ConfigObj(MainCfg)

def dm_order_http():
    '''
    主程序
    '''
    #获取参数
    xArg = sys.argv[1:]
    args_nums = len(xArg)
    if args_nums != 2:
        print 'Wrong Input!'
        return

    #获取处理文件时间和文件类型
    Ftime = xArg[0]
    Ftype = xArg[1]

    #获取FTP信息
    HOST = Cfg[Ftype]['HOST']
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

#     print "SDIR: ", SDIR
    for DIR in SDIR:
        #=======================================================================
        # hourly: order file sorted by year, one file per year. (from 1972)
        # daily, monthly: one single file.
        #=======================================================================
        date_s, date_e = ymd2date(Ftime)
        print DIR
        while date_s <= date_e:
            if DIR == 'hourly':
                Ymd = date_s.strftime('%Y%m%d')
                Url = urljoin(HOST, DIR, 'y'+Ymd[:4])
                date_s = date_s + relativedelta(years=1)
            else:
                Ymd = time.strftime('%Y%m%d', time.gmtime())
                Url = urljoin(HOST, DIR)
                date_s = date_e + relativedelta(years=1)
            # 拼接本地存储目录 和 订单文件
            if SDIR_IS_PATH.strip() == 'yes':
                FULL_ORDER_DIR = urljoin(ORDER_DIR, Ftype, DIR)
            elif SDIR_IS_PATH.strip() == 'no':
                FULL_ORDER_DIR = urljoin(ORDER_DIR, Ftype)

            if not os.path.exists(FULL_ORDER_DIR):
                os.makedirs(FULL_ORDER_DIR)

            html = getHtml(Url)
            if html is None:
                return

            #类的实例化, 获取文件名和大小的list
            dm = DM()
            dm.feed(html)
            dm.close()
            FileName, FileSize = dm.getStr()
#             for fn, fs in map(None, FileName, FileSize):
#                 print "DIR: %s\tFileName: %s\tFileSize: %s\tTime: %s" % (DIR, fn, fs, Ymd)
            FileName = [Url + '/' + eachline for eachline in FileName]
#             print "Url: %s\tFileName:%s" % (Url, FileName)

            # 把文件名和大小变为俩列，并增加回车符
            URL = zip(FileName, FileSize)
            URL = [' '.join(eachline) + '\n' for eachline in URL]
            #订单文件
            ORDER_FILE = urljoin(FULL_ORDER_DIR, Ymd + '.txt')
            print ORDER_FILE
            fp = open(ORDER_FILE, 'w')
            fp.writelines(URL)
            fp.close()


class DM(HTMLParser):

    '''
    网页解析
    '''
    def __init__(self):
        self.strlst = []
        self.strlst2 = []
        self.a = False
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.a = True

    def handle_endtag(self, tag):
        if tag == 'a':
            self.a = False

    def handle_data(self, data):
        if self.a:
            if not data.strip() == '':
                if '.dat' in data:
                    self.strlst.append(data.strip())
        if not self.a:
            if not data.strip() == '':
                if 'K' in data or 'M' in data:
                    strt = data.strip()
                    size = strt.split()[2]
                    if 'K' in size:
                        realsize= (float(size[:-1]) - 0.5) * 1024
                    elif 'M' in size:
                        realsize= (float(size[:-1]) - 0.5) * 1024 * 1024
                    self.strlst2.append(str(realsize))

    def getStr(self):
        return self.strlst, self.strlst2


def getHtml(url):
    '''
    获得网页
    '''
    opener = urllib2.build_opener(
        urllib2.HTTPHandler(),
        urllib2.HTTPSHandler(),
        urllib2.ProxyHandler({'https': 'http://user:pass@proxy:3128'}))
    urllib2.install_opener(opener)

    try:
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)
    except Exception, e:
        print '---Net ERROR!!!---'
        print str(e)
        return None
    html = resp.read()
    resp.close()
    return html

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

if __name__ == '__main__':

    print 'use conf', MainCfg
    dm_order_http()

