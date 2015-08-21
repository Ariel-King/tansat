# coding=UTF-8
__author__ = 'wangpeng'

import os, sys, re, shutil
import numpy as np
import math
from datetime import datetime
import time
from configobj import ConfigObj
from posixpath import join as urljoin
from dateutil.relativedelta import relativedelta

# 角度 -> 弧度
DEGREES_TO_RADIANS = math.pi / 180.0
# 弧度 -> 角度
RADIANS_TO_DEGREES = 180.0 / math.pi
# 地球平均半径
EARTH_MEAN_RADIUS_KM = 6371.009
# 地球极半径
EARTH_POLAR_RADIUS_KM = 6356.752
# 地球赤道半径
EARTH_EQUATOR_RADIUS_KM = 6378.137

# 配置文件信息，设置为全局
MainPath, MainFile = os.path.split(os.path.realpath(__file__))
# MainCfg = os.path.join(MainPath, MainFile.split('.')[0]+'.cfg')
MainCfg = os.path.join(MainPath, 'dp.cfg')
Cfg = ConfigObj(MainCfg)


def distance_GreatCircle_np(lat1, lon1, lat2, lon2):
    '''
    http://en.wikipedia.org/wiki/Great-circle_distance
    lat1, lon1, lat2, lon2 all are np.array
    '''
    delta_lon = lon1 - lon2

    distance = EARTH_EQUATOR_RADIUS_KM * np.arccos(
        np.sin(lat1 * DEGREES_TO_RADIANS) * np.sin(lat2 * DEGREES_TO_RADIANS) +
        np.cos(lat1 * DEGREES_TO_RADIANS) * np.cos(lat2 * DEGREES_TO_RADIANS) * np.cos(delta_lon * DEGREES_TO_RADIANS))
    return distance


def main():
    # 获取参数
    xArg = sys.argv[1:]

    # 参数个数目前为2个
    args_nums = len(xArg)
    if args_nums != 4:
        print 'input args nums error'
        return

    # 获取处理文件时间和文件类型
    Ftime = xArg[0]
    Ftype1 = xArg[1]
    Ftype2 = xArg[2]
    Frate = xArg[3]

    # 解析配置文件
    group = '%s-%s' % (Ftype1, Ftype2)
    DIFF_TIME = float(Cfg[group]['DIFF_TIME'])
    DIFF_DIST = float(Cfg[group]['DIFF_DIST'])

    I_DIR = Cfg[group]['I_DIR']
    O_DIR = Cfg[group]['O_DIR']
    siteFile = urljoin(I_DIR, Ftype1, 'SiteList.txt')

    print siteFile
    if os.path.isfile(siteFile):
        fp = open(siteFile, 'r')
        Lines = fp.readlines()
        fp.close()
    else:
        print u'站点列表文件不存在'
        return

    for Line in Lines:
        siteName = Line.split()[0].strip()
        siteLon = Line.split()[1].strip()
        siteLat = Line.split()[2].strip()
        # print siteName
        match = MATCH()
        date_s, date_e = ymd2date(Ftime)
        while date_s <= date_e:
            ymd = date_s.strftime('%Y%m%d')
            time_series1 = urljoin(I_DIR, Ftype1, siteName, 'time_series_' + Frate + '.txt')
            time_series2 = urljoin(I_DIR, Ftype2, ymd[:4], ymd + '.txt')
            # print time_series1, time_series2

            SiteData = match.ReadSite(time_series1, date_s)
            print time_series1, date_s
            SateData = match.ReadSate(time_series2, date_s)
            # print SiteData,SateData
            # print len(SiteData)
            print siteName
            if len(SiteData) == 0:
                print ymd, u'站点数据不存在'
                date_s = date_s + relativedelta(days=1)
                continue
            elif  len(SateData) == 0:
                print ymd, u'卫星数据不存在'
                date_s = date_s + relativedelta(days=1)
                continue

            for x in xrange(len(SiteData)):
                strTime = SiteData[x][0]
                site_xco2 = SiteData[x][1]
                newDate = datetime.strptime(strTime, "%Y-%m-%d %H:%M:%S")
                newDate1 = newDate + relativedelta(hours=-DIFF_TIME)
                newDate2 = newDate + relativedelta(hours=DIFF_TIME)
                FormatT1 = newDate1.strftime('%Y-%m-%d %H:%M:%S')
                FormatT2 = newDate2.strftime('%Y-%m-%d %H:%M:%S')

                # 第一轮进行时间筛选
                condition = np.logical_and(SateData['datetime'] >= FormatT1, SateData['datetime'] <= FormatT2)
                SateData = SateData[np.where(condition)]
                if len(SateData) == 0:
                    print ymd, u'时间不匹配'
                    continue

                # 第二轮进行距离筛选
                siteLonL = np.ones(len(SateData)) * float(siteLon)
                siteLatL = np.ones(len(SateData)) * float(siteLat)
                dis = distance_GreatCircle_np(siteLonL, siteLatL, SateData['lon'], SateData['lat'])
                SateData = SateData[np.where(dis <= DIFF_DIST)]
                dis = dis[np.where(dis <= DIFF_DIST)]
                if len(SateData) == 0:
                    print ymd, u'距离不匹配'
                    continue

                # print dis
                xco2 = np.mean(SateData['xco2'])
                xco2_nums = len(SateData['xco2'])
                dis_min = np.min(dis)
                Line = '%19s %15s %15.3f %15.3f %15.3f %15d\n' % (
                    strTime, siteName, site_xco2, xco2, dis_min, xco2_nums)
                print Line
                match.FileSave.append(Line)

            date_s = date_s + relativedelta(days=1)
        O_FILE = urljoin(O_DIR, Ftype1 + '-' + Ftype2 + '_' + Frate + '.txt')
        match.Write(O_FILE)


class MATCH():
    def __init__(self):

        self.FileSave = []

    def ReadSite(self, file, ymd):

        FileLines = []
        DATA_SITE = []
        FormatT1 = ymd.strftime('%Y-%m-%d') + ' ' + '00:00:00'
        FormatT2 = ymd.strftime('%Y-%m-%d') + ' ' + '23:59:59'
        if os.path.isfile(file):
            fp = open(file, 'r')
            fp.readline()
            Lines = fp.readlines()
            fp.close()

            for Line in Lines:
                dateT = Line.split()[0].strip()
                timeT = Line.split()[1].strip()
                mean = Line.split()[2].strip()

                FileLines.append([dateT + ' ' + timeT, mean])

            title = ['datetime', 'mean']
            dtype = ['S19'] + ['f4']
            ary = np.core.records.fromarrays(np.array(FileLines).transpose(),
                names=','.join(title),
                formats=','.join(dtype))
            condition = np.logical_and(ary['datetime'] >= FormatT1, ary['datetime'] <= FormatT2)
            condition = np.logical_and(condition, ~ np.isnan(ary['mean']))

            DATA_SITE = ary[np.where(condition)]

        return DATA_SITE


    def ReadSate(self, file, ymd):

        FileLines = []
        DATA_SATE = []
        FormatT1 = ymd.strftime('%Y-%m-%d') + ' ' + '00:00:00'
        FormatT2 = ymd.strftime('%Y-%m-%d') + ' ' + '23:59:59'
        if os.path.isfile(file):
            fp = open(file, 'r')
            fp.readline()
            Lines = fp.readlines()
            fp.close()

            for Line in Lines:
                dateT = Line.split()[0].strip()
                timeT = Line.split()[1].strip()
                xco2 = Line.split()[2].strip()
                lon = Line.split()[3].strip()
                lat = Line.split()[4].strip()

                FileLines.append([dateT + ' ' + timeT, xco2, lon, lat])

            title = ['datetime', 'xco2', 'lon', 'lat']
            dtype = ['S19'] + ['f4'] * 3
            ary = np.core.records.fromarrays(np.array(FileLines).transpose(),
                names=','.join(title),
                formats=','.join(dtype))
            condition = np.logical_and(ary['datetime'] >= FormatT1, ary['datetime'] <= FormatT2)
            condition = np.logical_and(condition, ~ np.isnan(ary['xco2']))
            DATA_SATE = ary[np.where(condition)]
        return DATA_SATE

    def Write(self, FileName):

        allLines = []
        DICT_D = {}

        if self.FileSave == []:
            return
        # 目录不存在则创建
        FilePath = os.path.dirname(FileName)
        if not os.path.exists(FilePath):
            os.makedirs(FilePath)

        Title = '%19s  %15s  %15s  %15s  %15s %15s\n' % (
            '[Time]', '[SiteName]', '[SiteCo2]', '[SateCo2]', '[DIS]', '[NUMS]')

        if os.path.isfile(FileName) and os.path.getsize(FileName) != 0:
            fp = open(FileName, 'r')
            fp.readline()
            Lines = fp.readlines()
            fp.close()
            # 使用字典特性，保证时间唯一，读取数据
            for Line in Lines:
                dateT = Line.split()[0].strip()
                timeT = Line.split()[1].strip()
                siteName = Line.split()[2].strip()
                site_xco2 = float(Line.split()[3].strip())
                xco2 = float(Line.split()[4].strip())
                dis_min = float(Line.split()[5].strip())
                xco2_nums = int(Line.split()[6].strip())
                # print dateT + ' ' + timeT, siteName, site_xco2, xco2, dis_min, xco2_nums
                key = '%19s %15s' % (dateT + ' ' + timeT, siteName)
                value = ' %15.3f %15.3f %15.3f %15d\n' % (site_xco2, xco2, dis_min, xco2_nums)
                DICT_D[key] = value
            # 添加或更改数据
            for Line in self.FileSave:
                dateT = Line.split()[0].strip()
                timeT = Line.split()[1].strip()
                siteName = Line.split()[2].strip()
                site_xco2 = float(Line.split()[3].strip())
                xco2 = float(Line.split()[4].strip())
                dis_min = float(Line.split()[5].strip())
                xco2_nums = int(Line.split()[6].strip())
                # print dateT + ' ' + timeT, siteName, site_xco2, xco2, dis_min, xco2_nums
                key = '%19s %15s' % (dateT + ' ' + timeT, siteName)
                value = ' %15.3f %15.3f %15.3f %15d\n' % (site_xco2, xco2, dis_min, xco2_nums)
                DICT_D[key] = value
            # 按照时间排序
            newLines = sorted(DICT_D.iteritems(), key=lambda d: d[0], reverse=False)

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

