# coding=UTF-8
__author__ = 'wangpeng'

import os, sys, re, shutil
import numpy as np
from datetime import datetime
import time
from configobj import ConfigObj
from posixpath import join as urljoin
from dateutil.relativedelta import relativedelta
import ds_PUB_LIB


# 配置文件信息，设置为全局
MainPath, MainFile = os.path.split(os.path.realpath(__file__))
# MainCfg = os.path.join(MainPath, MainFile.split('.')[0]+'.cfg')
MainCfg = os.path.join(MainPath, 'ds.cfg')
Cfg = ConfigObj(MainCfg)

dtype = {'names': ('date', 'time', 'mean', 'var', 'std', 'nums'),
         'formats': tuple(['S10', 'S8'] + ['f4'] * 3 + ['i4'])}

dname_Nan = ['date', 'time', 'mean', 'var', 'std', 'nums']
dtype_Nan = ['S10', 'S8'] + ['f4'] * 3 + ['i4']


def show_hours(date_s, Ftype):
    IDIR = Cfg[Ftype]['I_DIR']
    ODIR = Cfg[Ftype]['O_DIR_H']
    AERA = Cfg[Ftype]['L2S']

    TimeList = []
    DictData = {}
    for i in range(24):
        dateT1 = date_s + relativedelta(hours=i)
        TimeList.append(dateT1)

    for aera in AERA.keys():
        Line = []
        shortname = Cfg[Ftype]['L2S'][aera].decode('utf-8')
        ymd = date_s.strftime('%Y%m%d')
        FileName = urljoin(IDIR, aera, 'hours', ymd + '.txt')
        print FileName
        if os.path.isfile(FileName) and os.path.getsize(FileName) != 0:
            ary = np.loadtxt(FileName, dtype=dtype, skiprows=1).reshape((-1,))
        else:
            for i in range(24):
                t_str = '%s %s %f %f %f %d' % (ymd, '00:00:00', np.nan, np.nan, np.nan, 9999)
                Line.append([each.strip() for each in t_str.split()])
            ary = np.core.records.fromarrays(np.array(Line).transpose(),
                names=','.join(dname_Nan),
                formats=','.join(dtype_Nan))
        DictData[shortname] = ary
    # print DictData

    if not os.path.isdir(ODIR):
        os.makedirs(ODIR)
    # 平均值
    DictMean = {}
    color_dict = {}
    for eachkey in DictData.keys():
        DictMean[eachkey] = DictData[eachkey]['mean']
        print 'TimeList', len(TimeList), eachkey, len(DictMean[eachkey])

    DictVar = {}
    for eachkey in DictData.keys():
        DictVar[eachkey] = DictData[eachkey]['var']
        print 'TimeList', len(TimeList), eachkey, len(DictVar[eachkey])

    DictTitle1 = {'xlabel': 'x %s' % ymd, 'ylabel': 'mean', 'title': 'gga'}
    DictTitle2 = {'xlabel': 'x %s' % ymd, 'ylabel': 'Var', 'title': 'gga'}
    # ymd = time.strftime('%Y%m%d', time.localtime())

    Outimg1 = urljoin(ODIR, ymd + '_mean')
    Outimg2 = urljoin(ODIR, ymd + '_var')

    ds_PUB_LIB.draw_time_fig(TimeList, DictMean, Outimg1, DictTitle1, 'H')
    ds_PUB_LIB.draw_time_fig(TimeList, DictVar, Outimg2, DictTitle2, 'H')


def combine_day(FileList):
    data = []
    for file in FileList:
        if os.path.isfile(file):
            ary = np.loadtxt(file, dtype=dtype, skiprows=1).reshape((-1,))
        else:
            Line = []
            t_str = '%s %s %f %f %f %d' % ('9999', '9999', np.nan, np.nan, np.nan, 9999)
            Line.append([each.strip() for each in t_str.split()])
            ary = np.core.records.fromarrays(np.array(Line).transpose(),
                names=','.join(dname_Nan),
                formats=','.join(dtype_Nan))
        if data == []:
            data = ary
        else:
            data = np.concatenate((data, ary), axis=0)
    return data


def show_day(Ftype, Ftime):
    IDIR = Cfg[Ftype]['I_DIR']
    ODIR = Cfg[Ftype]['O_DIR_D']
    AERA = Cfg[Ftype]['L2S']

    TimeList = []
    DictData = {}
    date_s, date_e = ymd2date(Ftime)
    while date_s <= date_e:
        TimeList.append(date_s)
        date_s = date_s + relativedelta(days=1)
    for aera in AERA.keys():
        shortname = Cfg[Ftype]['L2S'][aera].decode('utf-8')
        print shortname
        FileList = []
        date_s, date_e = ymd2date(Ftime)
        while date_s <= date_e:
            ymd = date_s.strftime('%Y%m%d')
            FileName = urljoin(IDIR, aera, 'days', ymd + '.txt')
            FileList.append(FileName)
            date_s = date_s + relativedelta(days=1)
        data = combine_day(FileList)
        DictData[shortname] = data

    if not os.path.isdir(ODIR):
        os.makedirs(ODIR)
    print DictData
    # 平均值
    DictMean = {}
    for eachkey in DictData.keys():
        DictMean[eachkey] = DictData[eachkey]['mean']
        print 'TimeList', len(TimeList), eachkey, len(DictMean[eachkey])

        print len(TimeList), len(DictData[eachkey])

    # 偏差
    DictVar = {}
    for eachkey in DictData.keys():
        DictVar[eachkey] = DictData[eachkey]['var']
        print 'TimeList', len(TimeList), eachkey, len(DictVar[eachkey])

    DictTitle1 = {'xlabel': 'x %s' % ymd, 'ylabel': 'mean', 'title': 'gga'}
    DictTitle2 = {'xlabel': 'x %s' % ymd, 'ylabel': 'Var', 'title': 'gga'}
    # ymd = time.strftime('%Y%m%d', time.localtime())

    Outimg1 = urljoin(ODIR, ymd + '_mean')
    Outimg2 = urljoin(ODIR, ymd + '_var')

    ds_PUB_LIB.draw_time_fig(TimeList, DictMean, Outimg1, DictTitle1, 'D')
    ds_PUB_LIB.draw_time_fig(TimeList, DictVar, Outimg2, DictTitle2, 'D')


def main():
    # 获取参数
    xArg = sys.argv[1:]

    # 参数个数目前为2个
    args_nums = len(xArg)
    if args_nums != 3:
        print 'input error: args nums is three!'
        return

    # 获取处理文件时间和文件类型
    Ftime = xArg[0]
    Ftype = xArg[1]
    Frate = xArg[2]

    I_DIR = Cfg[Ftype]['I_DIR']
    O_DIR = Cfg[Ftype]['O_DIR']
    AERA = Cfg[Ftype]['L2S']

    DictData = {}
    for siteName in AERA.keys():
        date_s, date_e = ymd2date(Ftime)
        ShortName = Cfg[Ftype]['L2S'][siteName].decode('utf-8')
        I_FILE = urljoin(I_DIR, Ftype, siteName, 'time_series_' + Frate + '.txt')
        SiteData = ReadFile(I_FILE, date_s, date_e)
        print siteName
        if len(SiteData) != 0:
            DictData[ShortName] = SiteData
    # 平均值
    DictMean = {}
    for eachkey in DictData.keys():
        DictMean[eachkey] = DictData[eachkey]['mean']
    print DictMean
    stime = date_s.strftime('%Y%m%d')
    etime = date_e.strftime('%Y%m%d')
    DictTitle = {'xlabel': '%s-%s' % (stime, etime), 'ylabel': 'mean', 'title': '%s' % Ftype}

    O_FILE = urljoin(O_DIR, Ftype, stime + '_' + etime)
    TimeList = []
    for x in xrange(len(SiteData)):
        dateT = datetime.strptime(SiteData['time'][x], "%Y-%m-%d %H:%M:%S")
        print dateT
        TimeList.append(dateT)

    ds_PUB_LIB.draw_time_fig(TimeList, DictMean, O_FILE, DictTitle, Frate)


def ReadFile(i_file, date_s, date_e):
    Lines = []
    if os.path.isfile(i_file):
        fp = open(i_file, 'r')
        fp.readline()
        FileLines = fp.readlines()
        fp.close()
        # print i_file
        for Line in FileLines:
            # print Line
            dateT = Line.split()[0].strip()
            timeT = Line.split()[1].strip()
            xco2 = Line.split()[2].strip()
            var = Line.split()[3].strip()
            std = Line.split()[4].strip()
            nums = Line.split()[5].strip()

            Lines.append([dateT + ' ' + timeT, xco2, var, std, nums])

    title = ['time', 'mean', 'var', 'std', 'nums']
    dtype = ['S19'] + ['f4'] * 3 + ['i4']

    FormatT1 = date_s.strftime('%Y-%m-%d') + ' ' + '00:00:00'
    FormatT2 = date_e.strftime('%Y-%m-%d') + ' ' + '23:59:59'

    FileData = np.core.records.fromarrays(np.array(Lines).transpose(),
        names=','.join(title),
        formats=','.join(dtype))
    condition = np.logical_and(FileData['time'] >= FormatT1, FileData['time'] < FormatT2)
    DATA = FileData[np.where(condition)]
    return DATA


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
    main()

