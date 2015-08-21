# coding=UTF-8
__author__ = 'wangpeng'

import os, sys, re, log, shutil
from datetime import date, timedelta
from configobj import ConfigObj
from posixpath import join as urljoin
import ftplib, ftputil
import urllib, urllib2
from HTMLParser import HTMLParser
import tarfile
from zipfile import ZipFile

# 配置文件信息，设置为全局
MainPath, MainFile = os.path.split(os.path.realpath(__file__))
# MainCfg = os.path.join(MainPath, MainFile.split('.')[0]+'.cfg')
MainCfg = os.path.join(MainPath, 'dm.cfg')
Cfg = ConfigObj(MainCfg)


def main():
    '''
    主程序
    '''
    # 获取参数
    xArg = sys.argv[1:]
    args_nums = len(xArg)
    if args_nums != 1:
        print 'input error: args nums is one!'
        return

    # 获取处理文件类型
    Ftype = xArg[0]

    SERVER_DIR = Cfg[Ftype]['SDIR']
    SDIR_IS_PATH = Cfg[Ftype]['SDIR_IS_PATH']

    # 获取目录信息
    SDATA_DIR = Cfg['DIR']['SDATA']
    TDATA_DIR = Cfg['DIR']['TDATA']
    LOG = Cfg['DIR']['LOG']

    # 获取日志文件的路径
    LOG_DIR = os.path.split(LOG)[0]
    # 日志目录不存在创建
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    dm = DM()

    if Ftype == 'GGA':
        FULL_TDATA_DIR = urljoin(TDATA_DIR, Ftype)
        FULL_SDATA_DIR = urljoin(SDATA_DIR, Ftype)
        dm.move_gga(FULL_TDATA_DIR, FULL_SDATA_DIR)

    elif Ftype == 'WDCGG':
        FULL_TDATA_DIR = urljoin(TDATA_DIR, Ftype)
        FULL_SDATA_DIR = urljoin(SDATA_DIR, Ftype)
        dm.move_wdcgg(FULL_TDATA_DIR, FULL_SDATA_DIR)


class DM():

    def move_gga(self, SRC_DIR, DES_DIR):
        patZip = 'gga_\w+(\d{4})_\w+.txt.zip\Z'
        patTxt = 'gga_\w+(\d{4})_\w+.txt\Z'
        UNZIP_DIR = Cfg['DIR']['UNZIP']
        # 临时解压目录不存在创建
        if not os.path.exists(UNZIP_DIR):
            os.makedirs(UNZIP_DIR)

        # 遍历要迁移的目录
        Lst = sorted(os.listdir(SRC_DIR), reverse=False)
        for Line in Lst:
            FullPath = urljoin(SRC_DIR, Line)
            # 发现目录则递归
            if os.path.isdir(FullPath):
                self.move_gga(FullPath, DES_DIR)
            #处理tar文件
            elif os.path.isfile(FullPath) and 'tar.gz' in FullPath and '.lock' not in FullPath:
                if 'Z_CAWN_I_50136' in FullPath:
                    DIR = urljoin(DES_DIR, 'waliguan')
                elif 'Z_CAWN_I_52859' in FullPath:
                    DIR = urljoin(DES_DIR, 'mohe')
                elif 'guangzhou_lgr_12_0185' in FullPath:
                    DIR = urljoin(DES_DIR, 'guangzhou')
                elif 'tazhonglgr' in FullPath:
                    DIR = urljoin(DES_DIR, 'tazhong')
                elif 'xinjiang_lgr_12_0182' in FullPath:
                    DIR = urljoin(DES_DIR, 'xinjiang')
                else:
                    print 'ERROR SITE'
                    return

                print u'处理tar.gz文件：', FullPath
                # 打开tar.gz 文件
                tar = tarfile.open(FullPath)
                try:
                    tar.extractall(UNZIP_DIR)
                except Exception, e:
                    log.error('%s' % str(e))
                    if os.path.exists(UNZIP_DIR):
                        shutil.rmtree(UNZIP_DIR)
                    continue
                finally:
                    tar.close()

                #处理zip文件
                for tarinfo in tar:
                    FULL_UNZIP_FILE = urljoin(UNZIP_DIR, tarinfo.name)

                    if '.zip' in tarinfo.name[-4:]:
                        try:
                            DataFile = os.path.split(tarinfo.name)[1]
                            print u'    发现zip文件：', FULL_UNZIP_FILE
                            ReZip = re.match(patZip, DataFile)
                            if ReZip:
                                FULL_DES_DIR = urljoin(DIR, ReZip.group(1))
                                if not os.path.exists(FULL_DES_DIR):
                                    os.makedirs(FULL_DES_DIR)
                                with ZipFile(FULL_UNZIP_FILE, 'r') as myzip:
                                    myzip.extractall(FULL_DES_DIR)
                        except Exception, e:
                            log.error('%s %s' % (FULL_UNZIP_FILE, str(e)))
                    if '.txt' in tarinfo.name[-4:] and 'batch' not in tarinfo.name:
                        print u'    发现txt文件：', FULL_UNZIP_FILE
                        DataFile = os.path.split(tarinfo.name)[1]
                        if os.path.isfile(FULL_UNZIP_FILE):
                            ReTxt = re.match(patTxt, DataFile)
                            if ReTxt:
                                FULL_DES_DIR = urljoin(DIR, ReTxt.group(1))
                                if not os.path.exists(FULL_DES_DIR):
                                    os.makedirs(FULL_DES_DIR)
                                shutil.copy2(FULL_UNZIP_FILE, FULL_DES_DIR)
                if os.path.exists(UNZIP_DIR):
                    shutil.rmtree(UNZIP_DIR)
                os.unlink(FullPath)

    def move_wdcgg(self, SRC_DIR, DES_DIR):

        patH = '\w+.\w+.\w+.cn.co2.\w+.hr(\d{4}).dat'
        patM = '\w+.\w+.\w+.\w+.co2.\w+.mo.dat'
        patD = '\w+.\w+.\w+.\w+.co2.\w+.da.dat'

        # 遍历要迁移的目录
        Lst = sorted(os.listdir(SRC_DIR), reverse=False)
        for Line in Lst:
            FullPath = urljoin(SRC_DIR, Line)
            # 发现目录则递归
            if os.path.isdir(FullPath):
                self.move_wdcgg(FullPath, DES_DIR)
            # 处理tar文件
            elif os.path.isfile(FullPath) and '.lock' not in FullPath:
                # print FullPath
                ReH = re.match(patH, Line)
                ReM = re.match(patM, Line)
                ReD = re.match(patD, Line)
                if ReH:
                    # print FullPath, ReH.group(1)
                    FULL_DES_PATH = urljoin(DES_DIR, 'hourly', ReH.group(1))
                    if not os.path.exists(FULL_DES_PATH):
                        os.makedirs(FULL_DES_PATH)
                    try:
                        shutil.move(FullPath, FULL_DES_PATH)
                    except Exception, e:
                        print e
                        # print DES_DIR
                elif ReD:
                    print FullPath
                    FULL_DES_PATH = urljoin(DES_DIR, 'daily')
                    if not os.path.exists(FULL_DES_PATH):
                        os.makedirs(FULL_DES_PATH)
                    try:
                        shutil.move(FullPath, FULL_DES_PATH)
                    except Exception, e:
                        print e
                elif ReM:
                    print FullPath
                    FULL_DES_PATH = urljoin(DES_DIR, 'monthly')
                    if not os.path.exists(FULL_DES_PATH):
                        os.makedirs(FULL_DES_PATH)
                    try:
                        shutil.move(FullPath, FULL_DES_PATH)
                    except Exception, e:
                        print e
                else:
                    print 'FileName Format Error'


if __name__ == '__main__':
    '''
    获取程序同名的配置文件
    '''
    main()

