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

    # 参数个数目前为1个
    args_nums = len(xArg)
    if args_nums != 1:
        print ' args nums error'
        return

    # 获取处理文件时间和文件类型
    Ftype = xArg[0]

    # 解析配置文件
    I_DIR = Cfg[Ftype]['I_DIR']
    O_DIR = Cfg[Ftype]['O_DIR']

    # 一维LIST去重方法
    # l1 = ['b','c','d','b','c','a']
    # l2 = {}.fromkeys(l1).keys()

    SiteList = urljoin(O_DIR, Ftype,  'SiteList.txt')
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
        siteName =  siteLine.strip().split()[0]
        # 根据站点开始 结束时间 来处理数据，手动时可注释掉
        start_time = siteLine.strip().split()[3].replace('-', '')
        end_time = siteLine.strip().split()[4].replace('-','')
        Ftime = start_time + '-' + end_time
        print siteName, start_time, end_time
        date_s, date_e = ymd2date(Ftime)
        wdcgg = WDCGG()
        wdcgg.SiteName = siteName
        oFile = urljoin(O_DIR, Ftype, wdcgg.SiteName, 'time_series.txt')
        wdcgg.FindFile(I_DIR)
        wdcgg.ReadFile()
        wdcgg.Combine_S(date_s, date_e)
        wdcgg.Write_S(oFile)


class WDCGG():
    def __init__(self):

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
        tmpLines = {}

        for file in self.FileList:
            fp = open(file , 'r')
            Lines = fp.readlines()
            fp.close()
            # 获取文件的头信息所占行数
            for Line in Lines:
                if 'HEADER LINES:' in Line:
                    head_nums  = int(Line.split(':')[1].strip())
                    break
            # 读取文件数据体部分
            for newLine in Lines[head_nums:]:
                # 获取co2浓度值 小于0的过滤掉
                xco2 = float(newLine.split()[4])
                if xco2 < 0:
                    continue
                # 重新封装时间
                strTime = newLine.split()[0] + ' ' + newLine.split()[1] + ':00'

                # 24点进行转换第二天00点
                if ' 24:00' in strTime:
                    strTime = strTime.replace('24', '23')
                    newDate = datetime.strptime(strTime, "%Y-%m-%d %H:%M:%S")
                    newDate += relativedelta(hours=1)
                    strTime = newDate.strftime('%Y-%m-%d %H:%M:%S')

                # 使用字典特性保存值并去重复
                tmpLines[strTime] = xco2
        # 排序，并把字典转换为2维list
        self.FileLine = sorted(tmpLines.iteritems(), key=lambda d:d[0], reverse=False)
        # print self.FileLine[0][0]
        # print self.FileLine[-1][0]

        # list 变为矩阵
        title = ['time', 'xco2']
        dtype = ['S19'] + ['f4']
        ary = np.core.records.fromarrays(np.array(self.FileLine).transpose(),
            names=','.join(title),
            formats=','.join(dtype))
        condition = np.logical_and(ary['xco2'] > 0, ary['xco2'] < 600)
        self.FileData = ary[np.where(condition)]
        # print self.FileData


    def Combine_S(self, s_ymd, e_ymd):
        FormatT1 = s_ymd.strftime('%Y-%m-%d %H:%M:%S')
        FormatT2 = e_ymd.strftime('%Y-%m-%d %H:%M:%S')
        condition = np.logical_and(self.FileData['time'] >= FormatT1, self.FileData['time'] < FormatT2)
        DATA = self.FileData[np.where(condition)]
        for i in DATA:
            Line = '%19s  %15.6f \n' % (i['time'], i['xco2'])
            self.FileSave.append(Line)

    def Write_S(self, FileName):
        FilePath = os.path.dirname(FileName)
        if not os.path.exists(FilePath):
            os.makedirs(FilePath)

        Title = '%19s  %15s\n' % ('[Time]', '[Xco2]')

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

