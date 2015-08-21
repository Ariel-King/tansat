# coding=UTF-8
__author__ = 'wangpeng'

import os, sys, re
from datetime import  datetime
from configobj import ConfigObj
from posixpath import join as urljoin
from netCDF4 import Dataset

# 配置文件信息，设置为全局
MainPath, MainFile = os.path.split(os.path.realpath(__file__))
MainCfg = os.path.join(MainPath, 'dp.cfg')
Cfg = ConfigObj(MainCfg)


def main():
    # 获取参数
    xArg = sys.argv[1:]
    args_nums = len(xArg)
    if args_nums != 1:
        print 'input args nums error'
        return

    # 获取处理文件类型
    Ftype = xArg[0]

    # 从配置文件读取要处理的站点文件所在目录
    I_DIR = Cfg[Ftype]['I_DIR']
    # 处理结果存放根目录位置
    O_DIR = Cfg[Ftype]['O_DIR']
    # 处理结果存输出文件


    if Ftype == 'TCCON':
        # 数据完整的存放位置
        FULL_I_DIR = urljoin(I_DIR, Ftype)
        # 数据的匹配规则，按此规则查找
        pat = '\w+(\d{8})_(\d{8}).public.nc'
        # 输出的 站点列表文件
        ofile = urljoin(O_DIR, Ftype, 'SiteList.txt')
        print ofile

        # 开始处理
        tccon = PUBLIC()
        tccon.FindFile(FULL_I_DIR, pat)
        tccon.SiteList1()
        tccon.Write(ofile)

    elif 'WDCGG' in Ftype:
        pat = '.+\.dat'  # 数据的匹配规则，按此规则查找
        # 输出的 站点列表文件
        ofile = urljoin(O_DIR, Ftype, 'SiteList.txt')
        # 开始处理
        print ofile
        wdcgg = PUBLIC()
        wdcgg.FindFile(I_DIR, pat)
        wdcgg.SiteList2()
        wdcgg.Write(ofile)


class PUBLIC():
    def __init__(self):

        self.FileList = []
        self.FileSave = []

    # 查找TCCON数据的README.txt 文件, 已经删除pasadena01和karlsruhe01下的R0文件夹下的数据，被R1取代，修正过
    def FindFile(self, dir, pat):
        # 要查找当天文件的正则
        Lst = sorted(os.listdir(dir), reverse=False)
        for Line in Lst:
            FullPath = urljoin(dir, Line)
            # 如果是目录则进行递归
            if os.path.isdir(FullPath):
                self.FindFile(FullPath, pat)
            # 如果是文件则进行正则判断，并把符合规则的所有文件保存到List中
            elif os.path.isfile(FullPath):
                FileName = os.path.split(FullPath)[1]
                Re1 = re.match(pat, FileName)
                if Re1:
                    self.FileList.append(FullPath)

    def SiteList1(self):
        '''
        查找并创建 TCCON 数据的站点名，经纬度，开始结束时间信息
        '''
        # 从txt中获取经纬度信息，注掉了 暂时不用，从NC中获取，以后用来这看
        # patLines = '.+\(([-\.\d]+).+,([-\.\d]+).+\)\.'

        for file in self.FileList:
            ncFile = Dataset(file, 'r', format='NETCDF3_CLASSIC')  # 'NCETCDF4'
            Lon = ncFile.variables['long_deg'][0]
            Lat = ncFile.variables['lat_deg'][0]
            siteName = ncFile.getncattr('longName')
            start_date = ncFile.getncattr('start_date')
            end_date = ncFile.getncattr('end_date')
            ncFile.close()
            dateT_S = datetime.strptime(start_date, '%Y/%m/%d')
            dateT_E = datetime.strptime(end_date, '%Y/%m/%d')
            start_date = dateT_S.strftime('%Y-%m-%d')
            end_date = dateT_E.strftime('%Y-%m-%d')
            Line = '%17s  %15.6f  %15.6f  %15s  %15s\n' % (siteName, Lon, Lat, start_date, end_date)

            self.FileSave.append(Line)

    def SiteList2(self):
        '''
        查找并创建 WDCGG 数据的站点名，经纬度，开始结束时间信息
        '''
        tmpList1 = []
        tmpList2 = []
        tmpDict = {}
        for file in self.FileList:
            # 把文件名用 . 分割，第一部分作为站点名字
            FileName = os.path.split(file)[1]
            siteName = FileName.split('.')[0]
            # 打开文件，读取内容s
            fp = open(file, 'r')
            Lines = fp.readlines()
            fp.close()

            # 获取wdcgg的经纬度信息
            for line in Lines:
                if 'LATITUDE' in line:
                    Lat = line.split(':')[1].strip()
                elif 'LONGITUDE' in line:
                    Lon = line.split(':')[1].strip()
                else:
                    continue
            Line = '%17s  %15.6f  %15.6f\n' % (siteName, float(Lon), float(Lat))
            tmpList1.append(Line)

        # 去掉重复的站点
        for Line in tmpList1:
            if Line not in tmpList2:
                tmpList2.append(Line)
                # self.FileSave.append(Line)

        # 找同一站点文件
        for Line in tmpList2:
            siteName = Line.split()[0]
            Lon =  Line.split()[1]
            Lat =  Line.split()[2]
            for file in self.FileList:
                FileName = os.path.split(file)[1]
                if siteName in FileName:
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
                        strTime = newLine.split()[0]
                        # 使用字典特性保存值并去重复
                        tmpDict[strTime] = xco2
            # 排序，并把字典转换为2维list
            newList = sorted(tmpDict.iteritems(), key=lambda d:d[0], reverse=False)
            start_date =  newList[0][0]
            end_date = newList[-1][0]
            Line = '%17s  %15.6f  %15.6f  %15s  %15s\n' % (siteName, float(Lon), float(Lat), start_date, end_date)
            self.FileSave.append(Line)

    def Write(self, FileName):
        '''
        保存站点列表结果
        '''
        ODIR = os.path.dirname(FileName)
        if not os.path.exists(ODIR):
            os.makedirs(ODIR)
        fp = open(FileName, 'w')
        fp.writelines(self.FileSave)
        print "Writing Completed"
        fp.close()

if __name__ == '__main__':
    '''
    生成站点数据的站点清单
    '''
    main()

