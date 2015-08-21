# coding: UTF-8
'''
Created on 2012-2-21

@author: Administrator
'''

import sys
#sys.path.append("..")
import DBUtil

# init DB Connector
db14 = DBUtil.DBUtil()
db14.setDBConnector(db14.connector_DB14_tansat)

def insertTbl_datatype(lst):
    '''
    插入datatype
    lst :二维list, 每行代表一条记录，每个元素代表一个字段；
        一维则只插入一条记录
    '''
    if len(lst) == 0: return
    sql = """INSERT INTO datatype
        (id, name, type) 
        VALUES (%s) ON DUPLICATE KEY
        UPDATE name=VALUES(name), type=VALUES(type)""" % ','.join(['%s']*3)
    return db14.executeInsert(sql, lst)

def insertTbl_deviation_seq(lst):
    '''
    插入deviation_seq
    lst :二维list, 每行代表一条记录，每个元素代表一个字段
    '''
    if len(lst) == 0: return
    sql = """INSERT INTO deviation_seq
        (sat1, sensor1, sat2, sensor2, channel, timeType, display, dateTime, timeRange, referTemper, imgPath, type, field1) 
        VALUES (%s)""" % ','.join(['%s']*13)
    return db14.executeInsert(sql, lst)
           
def insertTbl_consistency(lst):
    '''
    插入consistency
    lst :二维list, 每行代表一条记录，每个元素代表一个字段
    '''
    if len(lst) == 0: return
    sql = """INSERT INTO consistency
        (sat1, sensor1, sat2, sensor2, channel, timeType, display, dateTime, timeRange, referTemper, imgPath, type, field1)
        VALUES (%s)""" % ','.join(['%s']*10)
    return db14.executeInsert(sql, lst)

def insertTbl_performance_track(lst):
    '''
    插入performance_track
    lst :二维list, 每行代表一条记录，每个元素代表一个字段
    '''
    if len(lst) == 0: return
    sql = """INSERT INTO performance_track
        (satellite, timeRange, first_display, second_display, last_display, dateTime, picPath)
        VALUES (%s)""" % ','.join(['%s']*7)
    return db14.executeInsert(sql, lst)
           
def selectTbl_daycalibration(picPath):
    '''
    查询 图像是否存在
    '''
    sql = """select count(*) from daycalibration where
          (picPath like '%%%s')""" % (picPath)
    res = db14.executeSearch(sql)
    return res[0][0]

def selectTbl_deviation_seq(picPath):
    '''
    查询 图像是否存在
    '''
    sql = """select count(*) 
            from deviation_seq where
            (imgPath like '%%%s')""" % (picPath)
    res = db14.executeSearch(sql)
    return res[0][0]

def selectTbl_consistency(picPath):
    '''
    查询 图像是否存在
    '''
    sql = """select count(*) 
            from consistency where
            (imgPath like '%%%s')""" % (picPath)
    res = db14.executeSearch(sql)
    return res[0][0]

def selectTbl_performance_track(picPath):
    '''
    查询 图像是否存在
    '''
    sql = """select count(*) 
            from performance_track where
            (picPath like '%%%s')""" % (picPath)
    res = db14.executeSearch(sql)
    return res[0][0]

def deleteTbl_daycalibration(sat1, sensor1, sat2, sensor2, ymd):
    '''
    删除daycalibration某天的数据
    ''' 
    sql = """delete from daycalibration where
        (sat1='%s' and sensor1='%s' and sat2='%s' and sensor2='%s' and dateTime='%s')""" % (sat1, sensor1, sat2, sensor2, ymd)
    res = db14.executeDelete(sql)
    return res

def deleteTbl_deviation_seq(sat1, sensor1, sat2, sensor2, ymd):
    '''
    删除deviation_seq某天的数据
    ''' 
    sql = """delete from deviation_seq where
        (sat1='%s' and sensor1='%s' and sat2='%s' and sensor2='%s' and dateTime='%s')""" % (sat1, sensor1, sat2, sensor2, ymd)
    res = db14.executeDelete(sql)
    return res

def deleteTbl_performance_track(sat, ymd):
    '''
    删除performance_track某天的数据
    ''' 
    sql = """delete from performance_track where
        (satellite='%s' and dateTime='%s')""" % (sat, ymd)
    res = db14.executeDelete(sql)
    return res
        
if __name__ == '__main__':
    pass
    
