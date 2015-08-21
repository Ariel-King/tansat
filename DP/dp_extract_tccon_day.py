# coding=UTF-8
__author__ = 'wangpeng'

import os, sys, re, shutil
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from configobj import ConfigObj
from posixpath import join as urljoin
from netCDF4 import Dataset



# 配置文件信息，设置为全局
MainPath, MainFile = os.path.split(os.path.realpath(__file__))
# MainCfg = os.path.join(MainPath, MainFile.split('.')[0]+'.cfg')
MainCfg = os.path.join(MainPath, 'dp.cfg')
Cfg = ConfigObj(MainCfg)


def main():
    # 获取参数
    xArg = sys.argv[1:]

    # 参数个数目前为3个
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
        siteName = siteLine.strip().split()[0]
        start_time = siteLine.strip().split()[3].replace('-', '')
        end_time = siteLine.strip().split()[4].replace('-','')
        Ftime = start_time + '-' + end_time
        print siteName, start_time, end_time
        date_s, date_e = ymd2date(Ftime)

        while date_s <= date_e:
            ymd = date_s.strftime('%Y%m%d')
            FULL_I_DIR =  urljoin(I_DIR, Ftype, siteName)
            # 输出文件在站点名下，按日输出，每天一个文件
            O_FILE = urljoin(O_DIR, Ftype, siteName, ymd[:4], ymd + '.txt')

            # 实例化WDCGG类
            tccon = TCCON()
            # 对类的全局变量赋值
            tccon.YMD = date_s
            tccon.SiteName = siteName
            # 开始处理
            tccon.FindFile(FULL_I_DIR)
            tccon.ReadFile()
            tccon.Filter()
            print  ymd,len(tccon.FileLine), len(tccon.FileData)
            tccon.Write(O_FILE)
            date_s = date_s + relativedelta(days=1)


class TCCON():

    def __init__(self):

        self.YMD = ''
        self.SiteName = ''
        self.FileList = []
        self.FileLine = []
        self.FileData = []
        self.FileSave = []

    def FindFile(self, dir):
        # 要查找当天文件的正则
        pat = '\w+(\d{8})_(\d{8}).public.nc\Z'
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
                if RePat:
                    self.FileList.append(FullPath)

    def ReadFile(self):
        '''
        读取TCCON数据,此数据一个站点一个文件
        '''
        if self.FileList == []:
            return

        FormatT1 = self.YMD.strftime('%Y-%m-%d 00:00:00')
        FormatT2 = self.YMD.strftime('%Y-%m-%d 23:59:59')

        for file in self.FileList:
            ncFile = Dataset(file, 'r', format='NETCDF3_CLASSIC')  # 'NCETCDF4'
            ncTime = ncFile.variables['time'][:]
            xco2_ppm = ncFile.variables['xco2_ppm'][:]
            ncFile.close()
            # print file

        for i in xrange(len(ncTime)):
            seconds = ncTime[i] * 24 * 60 * 60
            strTime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(seconds))
            # print strTime, FormatT1,FormatT2
            if FormatT1 <= strTime <= FormatT2:
                # print strTime, FormatT1,FormatT2
                self.FileLine.append([strTime, xco2_ppm[i]])
        # print self.FileLine[0], self.FileLine[-1]

    def Filter(self):
        '''
        对TCCON数据进行质量控制，阈值筛选
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
        # self.FileData = ary

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

