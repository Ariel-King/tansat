# coding=UTF-8
__author__ = 'wangpeng'

import os, sys, re, shutil
import numpy as np
from datetime import datetime
import time
from configobj import ConfigObj
from posixpath import join as urljoin
from dateutil.relativedelta import relativedelta

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
    if args_nums != 3:
        print 'input args nums error'
        return

    # 获取处理文件时间和文件类型
    Ftime = xArg[0]
    Ftype = xArg[1]
    Frate = xArg[2]

    # 解析配置文件
    O_DIR = Cfg[Ftype]['O_DIR']

    if 'TCCON' in Ftype or 'WDCGG' in Ftype or 'GGA' in Ftype:
        print Ftype
        # print 22222
        SiteList = urljoin(O_DIR, Ftype, 'SiteList.txt')
        if os.path.isfile(SiteList):
            fp = open(SiteList, 'r')
            SiteList = fp.readlines()
            fp.close()
        else:
            print 'SiteList.txt not found'
            return

        # 处理每个站点
        for siteLine in SiteList:
            # 根据站点清单，获取站点名
            if siteLine.strip() == '':
                continue
            siteName = siteLine.strip().split()[0]
            # 根据站点开始 结束时间 来处理数据，手动时可注释掉
            # start_time = siteLine.strip().split()[3].replace('-', '')
            # end_time = siteLine.strip().split()[4].replace('-','')
            # Ftime = start_time + '-' + end_time

            date_s, date_e = ymd2date(Ftime)
            print siteName, date_s, date_e

            O_FILE = urljoin(O_DIR, Ftype, siteName, 'time_series_' + Frate + '.txt')
            combine = COMBINE()
            if Ftype == 'GGA':  # 原值每天一个文件，需要遍历
                FULL_I_DIR = urljoin(O_DIR, Ftype, siteName)
                combine.FindFile(FULL_I_DIR, date_s, date_e)
            else:  # 所有原值均在time_series.txt
                I_FILE = urljoin(O_DIR, Ftype, siteName, 'time_series.txt')
                combine.FileList = [I_FILE]
            print combine.FileList
            combine.ReadFile()
            print combine.FileData
            combine.Combine(date_s, date_e, Frate)
            combine.Write(O_FILE)

    elif 'GOSAT' in Ftype:
        print Ftype
        date_s, date_e = ymd2date(Ftime)
        O_FILE = urljoin(O_DIR, Ftype, 'time_series_' + Frate + '.txt')
        FULL_I_DIR = urljoin(O_DIR, Ftype)
        combine = COMBINE()
        combine.FindFile(FULL_I_DIR, date_s, date_e)
        print combine.FileList
        combine.ReadFile()
        print combine.FileData
        combine.Combine(date_s, date_e, Frate)
        combine.Write(O_FILE)


class COMBINE:
    def __init__(self):

        self.FileList = []
        self.FileData = []
        self.FileSave = []

    def FindFile(self, dir, s_ymd, e_ymd):

        pat = '(\d{8})\.txt\Z'
        start_time = s_ymd.strftime('%Y%m%d')
        end_time = e_ymd.strftime('%Y%m%d')
        # 对目录进行递归查找，找出符合规则的所有文件
        Lst = sorted(os.listdir(dir), reverse=False)
        for Line in Lst:
            FullPath = urljoin(dir, Line)
            # 如果是目录则进行递归
            if os.path.isdir(FullPath):
                self.FindFile(FullPath, s_ymd, e_ymd)
            # 如果是文件则进行正则判断，并把符合规则的所有文件保存到List中
            elif os.path.isfile(FullPath):
                FileName = os.path.split(FullPath)[1]
                Re1 = re.match(pat, FileName)
                if Re1:
                    ymd = Re1.group(1)
                    # print ymd, start_time, end_time
                    if start_time <= ymd <= end_time:
                        self.FileList.append(FullPath)

    def ReadFile(self):

        AllLines = []
        if self.FileList == []:
            return
        for file in self.FileList:
            fp = open(file, 'r')
            fp.readline()
            Lines = fp.readlines()
            fp.close()
            for Line in Lines:
                dateT = Line.split()[0].strip()
                timeT = Line.split()[1].strip()
                xco2 = Line.split()[2].strip()
                AllLines.append([dateT + ' ' + timeT, xco2])

        title = ['time', 'xco2']
        dtype = ['S19'] + ['f4']

        self.FileData = np.core.records.fromarrays(np.array(AllLines).transpose(),
            names=','.join(title),
            formats=','.join(dtype))

    def Combine(self, s_ymd, e_ymd, type):
        if type == 'H':
            times = 24
        elif type == 'D':
            times = 1
        elif type == 'M':
            times = 1
            s_ymd = datetime(int(s_ymd.strftime('%Y')), int(s_ymd.strftime('%m')), 1)
            e_ymd = datetime(int(e_ymd.strftime('%Y')), int(e_ymd.strftime('%m')), 1)
        elif type == 'Y':
            times = 1
            s_ymd = datetime(int(s_ymd.strftime('%Y')), 1, 1)
            e_ymd = datetime(int(e_ymd.strftime('%Y')), 1, 1)
        else:
            print 'please input "H|D|M|Y"'
            return
        while s_ymd <= e_ymd:
            for i in range(times):

                if type == 'H':
                    dateT1 = s_ymd + relativedelta(hours=i)
                    dateT2 = s_ymd + relativedelta(hours=i + 1)
                elif type == 'D':
                    dateT1 = s_ymd + relativedelta(days=i)
                    dateT2 = s_ymd + relativedelta(days=i + 1)
                elif type == 'M':
                    dateT1 = s_ymd + relativedelta(months=i)
                    dateT2 = s_ymd + relativedelta(months=i + 1)
                elif type == 'Y':
                    dateT1 = s_ymd + relativedelta(years=i)
                    dateT2 = s_ymd + relativedelta(years=i + 1)

                # print dateT1, dateT2
                FormatT1 = dateT1.strftime('%Y-%m-%d %H:%M:%S')
                FormatT2 = dateT2.strftime('%Y-%m-%d %H:%M:%S')

                FormatTT = dateT1.strftime('%Y-%m-%d %H:%M:%S')
                # print FormatT1, FormatT2
                if len(self.FileData) != 0:
                    condition = np.logical_and(self.FileData['time'] >= FormatT1, self.FileData['time'] < FormatT2)
                    DATA = self.FileData[np.where(condition)]
                    Nums = len(DATA)

                    if Nums != 0:
                        mean = np.mean(DATA['xco2'])
                        var = np.var(DATA['xco2'])
                        std = np.std(DATA['xco2'])
                        Line = '%19s  %15.6f  %15.6f  %15.6f  %15d\n' % (FormatTT, mean, var, std, Nums)
                        self.FileSave.append(Line)
                    else:
                        Line = '%19s  %15s  %15s  %15s  %15d\n' % (FormatTT, np.nan, np.nan, np.nan, Nums)
                        self.FileSave.append(Line)
                else:
                    Line = '%19s  %15s  %15s  %15s  %15d\n' % (FormatTT, np.nan, np.nan, np.nan, 0)
                    self.FileSave.append(Line)

            if type == 'M':
                s_ymd = s_ymd + relativedelta(months=1)
            elif type == 'Y':
                s_ymd = s_ymd + relativedelta(years=1)
            else:
                s_ymd = s_ymd + relativedelta(days=1)


    def Write(self, FileName):

        allLines = []
        DICT_D = {}
        FilePath = os.path.dirname(FileName)
        if not os.path.exists(FilePath):
            os.makedirs(FilePath)

        Title = '%19s  %15s  %15s  %15s  %15s\n' % ('[Time]', '[Mean]', '[Var]', '[Std]', '[Nums]')
        if os.path.isfile(FileName) and os.path.getsize(FileName) != 0:
            fp = open(FileName, 'r')
            fp.readline()
            Lines = fp.readlines()
            fp.close()
            # 使用字典特性，保证时间唯一，读取数据
            for Line in Lines:
                DICT_D[Line[:19]] = Line[19:]
            # 添加或更改数据
            for Line in self.FileSave:
                DICT_D[Line[:19]] = Line[19:]
            # 按照时间排序
            newLines = sorted(DICT_D.iteritems(), key=lambda d:d[0], reverse=False)

            for i in xrange(len(newLines)):
                allLines.append(str(newLines[i][0]) + str(newLines[i][1]))
            fp = open(FileName, 'w')
            fp.write(Title)
            fp.writelines(allLines)
            fp.close()
        else:
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


