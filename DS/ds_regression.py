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


def main():
    # 获取参数
    xArg = sys.argv[1:]

    # 参数个数目前为4个
    args_nums = len(xArg)
    if args_nums != 4:
        print 'input args num error'
        return

    # 获取处理文件时间和文件类型
    Ftime = xArg[0]
    Ftype1 = xArg[1]
    Ftype2 = xArg[2]
    Frate = xArg[3]

    # 解析配置文件
    group = '%s-%s' % (Ftype1, Ftype2)
    I_DIR = Cfg[group]['I_DIR']
    O_DIR = Cfg[group]['O_DIR']

    date_s, date_e = ymd2date(Ftime)
    I_FILE = urljoin(I_DIR, group + '_' + Frate + '.txt')
    O_FILE = urljoin(I_DIR, group + '_' + Frate)
    DATA = ReadFile(I_FILE, date_s, date_e)
    print DATA

    DictTitle = {'xlabel': 'Site CO2', 'ylabel': 'Sate CO2', 'title': '%s-%s' % (Ftype1, Ftype2)}
    ds_PUB_LIB.draw_Scatter(DATA['SiteCo2'], DATA['SateCo2'], O_FILE, DictTitle, '', '')
    # print DATA


def ReadFile(file, ymd_s, ymd_e):

    FileLines = []
    DATA = []
    FormatT1 = ymd_s.strftime('%Y-%m-%d') + ' ' + '00:00:00'
    FormatT2 = ymd_e.strftime('%Y-%m-%d') + ' ' + '23:59:59'
    if os.path.isfile(file):
        fp = open(file, 'r')
        fp.readline()
        Lines = fp.readlines()
        fp.close()

        for Line in Lines:
            dateT = Line.split()[0].strip()
            timeT = Line.split()[1].strip()
            SiteCo2 = Line.split()[3].strip()
            SateCo2 = Line.split()[4].strip()

            FileLines.append([dateT + ' ' + timeT, SiteCo2, SateCo2])

        title = ['datetime', 'SiteCo2', 'SateCo2']
        dtype = ['S19'] + ['f4'] * 2
        ary = np.core.records.fromarrays(np.array(FileLines).transpose(),
            names=','.join(title),
            formats=','.join(dtype))
        condition = np.logical_and(ary['datetime'] >= FormatT1, ary['datetime'] <= FormatT2)
        # condition = np.logical_and(condition, ~ np.isnan(ary['mean']))

        DATA = ary[np.where(condition)]

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

