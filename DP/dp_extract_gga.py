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
        date_s, date_e = ymd2date(Ftime)
        siteName = siteLine.strip().split()[0]
        print siteName
        while date_s <= date_e:
            ymd = date_s.strftime('%Y%m%d')
            FULL_I_DIR = urljoin(I_DIR, Ftype, siteName)
            O_FILE = urljoin(O_DIR, Ftype, siteName, ymd[:4], ymd + '.txt')

            # 实例化GGA类
            gga = GGA()
            # 类中的全局变量赋值
            gga.YMD = date_s
            gga.SiteName = siteName

            # 开始提取文件
            gga.FindFile(FULL_I_DIR)
            gga.ReadFile()
            gga.Filter()
            gga.Write(O_FILE)
            print ymd, len(gga.FileData)
            date_s = date_s + relativedelta(days=1)


class GGA():
    def __init__(self):

        self.YMD = ''
        self.SiteName = ''
        self.FileList = []
        self.FileLine = []
        self.FileData = []
        self.FileSave = []

    def FindFile(self, dir):

        # 拼接数据上的日期格式，当天
        StrYmd1 = self.YMD.strftime('%d%b%Y')
        # 拼接数据上的日期格式，昨天
        yesterday = self.YMD - relativedelta(days=1)
        StrYmd2 = yesterday.strftime('%d%b%Y')
        # 要查找当天文件的正则
        patFile1 = '\Agga_%s_f000(\d{1}).txt\Z' % StrYmd1
        patFile2 = '\Agga_%s_f000(\d{1}).txt\Z' % StrYmd2
        # 对目录进行递归查找，找出符合规则的所有文件
        Lst = sorted(os.listdir(dir), reverse=True)
        for Line in Lst:
            FullPath = urljoin(dir, Line)
            # 如果是目录则进行递归
            if os.path.isdir(FullPath):
                self.FindFile(FullPath)
            # 如果是文件则进行正则判断，并把符合规则的所有文件保存到List中
            elif os.path.isfile(FullPath):
                FileName = os.path.split(FullPath)[1]
                R1 = re.match(patFile1, FileName)
                R2 = re.match(patFile2, FileName)
                if R1:
                    self.FileList.append(FullPath)
                if R2:
                    self.FileList.append(FullPath)

    def ReadFile(self):
        '''
        读取GGA数据，只获取00点到24点的数据保存为LIST
        '''
        if self.FileList == []:
            return

        if 'mohe' in self.SiteName:
            time1 = self.YMD.strftime('%d/%m/%y') + ' ' + '00:00:00'
            time2 = self.YMD.strftime('%d/%m/%y') + ' ' + '23:59:59'
        else:
            time1 = self.YMD.strftime('%m/%d/%y') + ' ' + '00:00:00'
            time2 = self.YMD.strftime('%m/%d/%y') + ' ' + '23:59:59'

        # 读取当天查找到的所有文件
        for file in self.FileList:
            fp = open(file, 'r')
            fp.readline()
            fp.readline()
            lines = fp.readlines()
            fp.close()
            # 把文件后面的无用信息过滤掉
            for line in lines:
                if not line.startswith('----'):
                    # 进行时间过滤00点到24点之间的数据保留

                    if time1 <= line.strip()[:17] <= time2:
                        # 保存为2维的LIST
                        # 把每一行放到LIST中
                        # newLine = line.split(',')
                        newLine = [each.strip() for each in line.split(',')]
                        # 取出时间，更改格式
                        # print newLine[0]
                        strTime = newLine[0]
                        if 'mohe' in self.SiteName:
                            dateT = datetime.strptime(strTime, '%d/%m/%y %H:%M:%S.%f')
                        else:
                            dateT = datetime.strptime(strTime, '%m/%d/%y %H:%M:%S.%f')

                        FormatT = dateT.strftime('%Y-%m-%d %H:%M:%S')
                        newLine[0] = FormatT
                        # print newLine[0]
                        self.FileLine.append(newLine)

    def Filter(self):
        '''
        对GGA数据进行质量控制，阈值筛选
        '''
        if self.FileLine == []:
            return
        title1 = ["time", "CH4_ppm", "CH4_ppm_se",
                  "H2O_ppm", "H2O_ppm_se",
                  "xco2", "CO2_ppm_se",
                  "CH4_DRY_ppm", "CH4_DRY_ppm_se",
                  "CO2_DRY_ppm", "CO2_DRY_ppm_se",
                  "GasP_torr", "GasP_torr_se", "GasT_C", "GasT_C_se",
                  "AmbT_C", "AmbT_C_se",
                  "RD0_us", "RD0_us_se", "RD1_us", "RD1_us_se",
                  "Fit_Flag", "MIU_valve", "MIU_desc"]

        title2 = ["time", "CH4_ppm", "CH4_ppm_se",
                  "H2O_ppm", "H2O_ppm_se",
                  "xco2", "CO2_ppm_se",
                  "CH4_DRY_ppm", "CH4_DRY_ppm_se",
                  "CO2_DRY_ppm", "CO2_DRY_ppm_se",
                  "GasP_torr", "GasP_torr_se", "GasT_C", "GasT_C_se",
                  "AmbT_C", "AmbT_C_se",
                  "RD0_us", "RD0_us_se", "RD1_us", "RD1_us_se",
                  "Fit_Flag"]

        dtype1 = ['S19'] + ['f4'] * 20 + ['i4'] * 2 + ['S2']
        dtype2 = ['S19'] + ['f4'] * 20 + ['i4']

        # 找到了文件，并且文件内容不为空则进行质量控制
        if len(self.FileLine) != 0:

            if 'tazhong' in self.SiteName:
                ary = np.core.records.fromarrays(np.array(self.FileLine).transpose(),
                    names=','.join(title1),
                    formats=','.join(dtype1))
            else:
                ary = np.core.records.fromarrays(np.array(self.FileLine).transpose(),
                    names=','.join(title2),
                    formats=','.join(dtype2))


            THHOLD_GasP_torr_L = Cfg['GGA']['THHOLD_GasP_torr_L']
            THHOLD_GasP_torr_H = Cfg['GGA']['THHOLD_GasP_torr_H']
            THHOLD_GasT_C_L = Cfg['GGA']['THHOLD_GasT_C_L']
            THHOLD_GasT_C_H = Cfg['GGA']['THHOLD_GasT_C_H']
            THHOLD_RD0_us_L = Cfg['GGA']['THHOLD_RD0_us_L']
            THHOLD_RD0_us_H = Cfg['GGA']['THHOLD_RD0_us_H']
            THHOLD_RD1_us_L = Cfg['GGA']['THHOLD_RD1_us_L']
            THHOLD_RD1_us_H = Cfg['GGA']['THHOLD_RD1_us_H']
            THHOLD_xco2_L = Cfg['GGA']['THHOLD_xco2_L']
            THHOLD_xco2_H = Cfg['GGA']['THHOLD_xco2_H']

            condition = np.logical_and(ary['GasP_torr'] >= int(THHOLD_GasP_torr_L), ary['GasP_torr'] <= int(THHOLD_GasP_torr_H))
            condition = np.logical_and(condition, ary['GasT_C'] >= int(THHOLD_GasT_C_L))
            condition = np.logical_and(condition, ary['GasT_C'] <= int(THHOLD_GasT_C_H))  # 温度过高后的预警（待）
            condition = np.logical_and(condition, ary['RD0_us'] >= int(THHOLD_RD0_us_L))   # Original: 10
            condition = np.logical_and(condition, ary['RD0_us'] <= int(THHOLD_RD0_us_H))
            condition = np.logical_and(condition, ary['RD1_us'] >= int(THHOLD_RD1_us_L))
            condition = np.logical_and(condition, ary['RD1_us'] <= int(THHOLD_RD1_us_H))
            condition = np.logical_and(condition, ary['xco2'] >= int(THHOLD_xco2_L))   # Original: 350
            condition = np.logical_and(condition, ary['xco2'] <= int(THHOLD_xco2_H))
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

