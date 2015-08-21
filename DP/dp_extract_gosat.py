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
import h5py

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

    date_s, date_e = ymd2date(Ftime)

    while date_s <= date_e:
        ymd = date_s.strftime('%Y%m%d')
        FULL_I_DIR = urljoin(I_DIR, Ftype)
        O_FILE = urljoin(O_DIR, Ftype, ymd[:4], ymd + '.txt')

        if Ftype == 'GOSAT_GER':
            pat = '.+%s.+nc\Z' % ymd
            gosat = GOSAT()
            gosat.FindFile(FULL_I_DIR, pat)
            gosat.ReadGer()
            gosat.Write(O_FILE)
            print O_FILE

        elif Ftype == 'GOSAT_JAP':
            pat = '.+%s.+h5\Z' % ymd
            gosat = GOSAT()
            gosat.FindFile(FULL_I_DIR, pat)
            gosat.ReadJap()
            gosat.Write(O_FILE)
            print O_FILE

        else:
            print 'File Type Error'
            return
        date_s = date_s + relativedelta(days=1)


class GOSAT():
    def __init__(self):

        self.FileList = []
        self.FileLine = []
        self.FileData = []
        self.FileSave = []

    def FindFile(self, dir, pat):

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
                Re1 = re.match(pat, FileName)
                if Re1:
                    self.FileList.append(FullPath)

    def ReadGer(self):
        '''
        读取德国GOSAT数据
        '''
        if self.FileList == []:
            return
        for file in self.FileList:
            h5File = h5py.File(file, 'r')
            h5_Lon = h5File.get('longitude')[:]
            h5_Lat = h5File.get('latitude')[:]
            h5_xco2 = h5File.get('xco2')[:]
            h5_time = h5File.get('time')[:]
            h5File.close()

            if len(h5_time) != 0:
                for i in xrange(len(h5_time)):
                    strTime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(h5_time[i]))
                    self.FileLine.append([strTime, h5_xco2[i], h5_Lon[i], h5_Lat[i]])
        if self.FileLine != []:
            title = ['time', 'xco2', 'lon', 'lat']
            dtype = ['S19'] + ['f4'] * 3
            ary = np.core.records.fromarrays(np.array(self.FileLine).transpose(),
                names=','.join(title),
                formats=','.join(dtype))
            condition = np.logical_and(ary['xco2'] > 0, ary['xco2'] < 600)
            self.FileData = ary[np.where(condition)]

    def ReadJap(self):
        '''
        读取日本GOSAT数据
        '''
        if self.FileList == []:
            return
        for file in self.FileList:
            h5File = h5py.File(file, 'r')
            h5_Lon = h5File.get('/Data/geolocation/longitude')[:]
            h5_Lat = h5File.get('/Data/geolocation/latitude')[:]
            h5_xco2 = h5File.get('/Data/mixingRatio/XCO2')[:]
            h5_time = h5File.get('/scanAttribute/time')[:]
            h5File.close()
            if len(h5_time) != 0:
                for i in xrange(len(h5_time)):
                    strTime = h5_time[i][:-4]
                    # strTime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(h5_time[i]))
                    self.FileLine.append([strTime, h5_xco2[i], h5_Lon[i], h5_Lat[i]])
                # print self.Line
        #
        if self.FileLine != []:
            title = ['time', 'xco2', 'lon', 'lat']
            dtype = ['S19'] + ['f4'] * 3
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
            Line = '%19s  %15.6f %15.6f %15.6f\n' % (self.FileData['time'][i], self.FileData['xco2'][i],
                                                     self.FileData['lon'][i], self.FileData['lat'][i])
            self.FileSave.append(Line)

        Title = '%19s  %15s  %15s  %15s\n' % ('[time]', '[xco2]', '[lon]', '[lat]')
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

