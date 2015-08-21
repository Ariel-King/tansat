# coding=UTF-8
__author__ = 'wangpeng'

import os, sys, re, shutil
import numpy as np
from datetime import datetime
import time
from configobj import ConfigObj
from posixpath import join as urljoin
from dateutil.relativedelta import relativedelta

import ftplib, ftputil
import urllib, urllib2
from HTMLParser import HTMLParser
import tarfile
from zipfile import ZipFile

# 配置文件信息，设置为全局
MainPath, MainFile = os.path.split(os.path.realpath(__file__))
# MainCfg = os.path.join(MainPath, MainFile.split('.')[0]+'.cfg')
MainCfg = os.path.join(MainPath, 'dp.cfg')
Cfg = ConfigObj(MainCfg)


def main():
    # 获取参数
    xArg = sys.argv[1:]

    # 参数个数目前为2个
    args_nums = len(xArg)
    if args_nums != 2:
        print ' args nums error'
        return

    # 获取处理文件时间和文件类型
    Ftime = xArg[0]
    Ftype = xArg[1]

    # 解析配置文件
    I_DIR = Cfg[Ftype]['I_DIR']
    O_DIR = Cfg[Ftype]['O_DIR']

    # 一维LIST去重方法
    # l1 = ['b','c','d','b','c','a']
    # l2 = {}.fromkeys(l1).keys()

    SiteList = urljoin(O_DIR, Ftype, 'SiteList.txt')
    if os.path.exists(SiteList):
        fp = open(SiteList, 'r')
        SiteList = fp.readlines()
        fp.close()
    else:
        print u'站点列表文件不存在'
        return

    for siteLine in SiteList:
        if siteLine.strip() == '':
            continue
        siteName = siteLine.strip().split()[0]

        # 根据站点开始 结束时间 来处理数据，手动时可注释掉
        # start_time = siteLine.strip().split()[3].replace('-', '')
        # end_time = siteLine.strip().split()[4].replace('-','')
        # Ftime = start_time + '-' + end_time
        date_s, date_e = ymd2date(Ftime)

        while date_s <= date_e:
            ymd = date_s.strftime('%Y%m%d')
            # 小时的WDCGG数据按年来存放
            if Ftype == 'WDCGG_H':
                FULL_I_DIR = urljoin(I_DIR, ymd[:4])
            else:
                # 日和月数据直接存放
                FULL_I_DIR = urljoin(I_DIR)
            # 输出文件在站点名下，按日输出，每天一个文件
            O_FILE = urljoin(O_DIR, Ftype, siteName, ymd[:4], ymd + '.txt')

            # 实例化WDCGG类
            wdcgg = WDCGG()
            # 对类的全局变量赋值
            wdcgg.YMD = date_s
            wdcgg.SiteName = siteName
            print FULL_I_DIR
            # 开始处理
            wdcgg.FindFile(FULL_I_DIR)
            wdcgg.ReadFile()
            wdcgg.Filter()
            print siteName, ymd, len(wdcgg.FileLine), len(wdcgg.FileData)

            wdcgg.Write(O_FILE)
            date_s = date_s + relativedelta(days=1)


class WDCGG():
    def __init__(self):

        self.YMD = ''
        self.SiteName = ''
        self.FileList = []
        self.FileLine = []
        self.FileData = []
        self.FileSave = []

    def FindFile(self, dir):
        # 要查找当天文件的正则
        pat = '.+\.dat\Z'
        # 对目录进行递归查找，找出符合规则的所有文件
        Lst = sorted(os.listdir(dir), reverse=False)
        for Line in Lst:
            FullPath = urljoin(dir, Line)
            # 如果是目录则进行递归
            if os.path.isdir(FullPath):
                self.FindFile(FullPath)
            # 如果是文件则进行正则判断，并把符合规则的所有文件保存到List中
            elif os.path.isfile(FullPath):
                FileName = os.path.split(FullPath)[1]
                RePat = re.match(pat, FileName)
                if RePat and self.SiteName in FileName:
                    self.FileList.append(FullPath)

    def ReadFile(self):
        '''
        读取WDCGG数据，只获取00点到24点的数据保存为LIST
        '''
        if self.FileList == []:
            return

        FormatT1 = self.YMD.strftime('%Y-%m-%d 00:00:00')
        FormatT2 = self.YMD.strftime('%Y-%m-%d 23:59:59')
        tmpLines = {}
        for file in self.FileList:
            fp = open(file, 'r')
            Lines = fp.readlines()
            fp.close()
            # 获取文件的头信息所占行数
            for Line in Lines:
                if 'HEADER LINES:' in Line:
                    head_nums = int(Line.split(':')[1].strip())
                    break
            # 读取文件数据体部分
            for newLine in Lines[head_nums:]:
                # 重新封装时间, 第一、二 列为日期和时间
                strTime = newLine.split()[0] + ' ' + newLine.split()[1] + ':00'

                # 获取co2浓度值 小于0的过滤掉,文件第五列
                xco2 = float(newLine.split()[4])
                if xco2 < 0:
                    continue

                # 神人也，4月份有31天，这也是没办法这么过滤一下
                # if '04-31' in strTime or '06-31' in strTime or '09-31' in strTime or '11-31' in strTime:
                #     continue

                # 24点进行转换第二天00点
                if ' 24:00' in strTime:
                    strTime = strTime.replace('24', '23')
                    try:
                        newDate = datetime.strptime(strTime, '%Y-%m-%d %H:%M:%S')
                        newDate += relativedelta(hours=1)
                        strTime = newDate.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception, e:
                        print u'日期格式错误', strTime
                        continue
                # 使用字典特性保存值并去重复
                # print strTime, FormatT1, FormatT2
                if FormatT1 <= strTime <= FormatT2:
                    # print strTime, FormatT1, FormatT2
                    tmpLines[strTime] = xco2

        # 排序，并把字典转换为2维list
        self.FileLine = sorted(tmpLines.iteritems(), key=lambda d: d[0], reverse=False)
        # print self.FileLine[0][0]
        # print self.FileLine[-1][0]

    def Filter(self):
        '''
        对WDCGG数据进行质量控制，阈值筛选
        '''
        if self.FileLine == []:
            return
        title = ['time', 'xco2']
        dtype = ['S19'] + ['f4']
        ary = np.core.records.fromarrays(np.array(self.FileLine).transpose(),
            names=','.join(title),
            formats=','.join(dtype))
        condition = np.logical_and(ary['xco2'] > 0, ary['xco2'] < 600)
        self.FileData = ary[np.where(condition)]

    def Write(self, FileName):
        '''
        写入当天质量控制后的CO2数据
        '''
        if len(self.FileData) == 0:
            return

        FilePath = os.path.dirname(FileName)
        if not os.path.exists(FilePath):
            os.makedirs(FilePath)

        # DATA 变为 LIST
        for i in xrange(len(self.FileData['time'])):
            Line = '%19s  %15.6f\n' % (self.FileData['time'][i], self.FileData['xco2'][i])
            self.FileSave.append(Line)

        Title = '%19s  %15s\n' % ('[time]', '[xco2]')
        fp = open(FileName, 'w')
        fp.write(Title)
        fp.writelines(self.FileSave)
        fp.close()


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
    '''
    获取程序同名的配置文件
    '''
    main()

